"""Worktree-based workspace management for feature development."""

import asyncio
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from ..config import FeatureWorkflowConfig
from ..models.workspace import WorkspaceMetadata, WorkspaceList, WorkspaceStatus, LinearIssue, GitInfo
from .git_manager import GitManager


class WorkspaceManager:
    """Manages git worktree-based feature development workspaces."""
    
    def __init__(self, config: FeatureWorkflowConfig):
        self.config = config
        self.git_manager = GitManager(config)
        self.metadata_dir = config.worktrees_metadata_dir
        self.active_workspace_file = config.active_workspace_file
    
    async def create_workspace(
        self,
        issue_id: str,
        description: str,
        base_branch: str = "main",
        repo_path: Path = None
    ) -> WorkspaceMetadata:
        """Create a new feature workspace using git worktrees."""
        # Ensure we have a git repository
        repo = await self.git_manager.ensure_repository(repo_path)
        repo_path = Path(repo.working_dir)
        
        # Generate workspace name and branch name
        workspace_name = self._generate_workspace_name(issue_id, description)
        branch_name = f"feature/{workspace_name}"
        
        # Check if workspace already exists
        existing_workspace = await self.get_workspace(workspace_name)
        if existing_workspace:
            raise ValueError(f"Workspace {workspace_name} already exists")
        
        # Check workspace limit
        existing_workspaces = await self.list_workspaces()
        if len(existing_workspaces.workspaces) >= self.config.workspace.max_worktrees:
            raise ValueError(f"Maximum number of worktrees ({self.config.workspace.max_worktrees}) reached")
        
        # Create worktree
        worktree_path = await self.git_manager.create_worktree_for_feature(
            repo=repo,
            feature_name=workspace_name,
            branch_name=branch_name,
            base_branch=base_branch
        )
        
        # Create workspace metadata
        linear_issue = LinearIssue(id=issue_id, title=description)
        git_info = GitInfo(
            repo_url=repo.remotes[0].url if repo.remotes else "",
            base_branch=base_branch,
            branch_name=branch_name,
            worktree_path=worktree_path,
            is_worktree=True
        )
        
        metadata = WorkspaceMetadata(
            name=workspace_name,
            path=worktree_path,
            description=description,
            issue=linear_issue,
            git=git_info,
            main_repo_path=repo_path
        )
        
        # Save metadata
        await self._save_workspace_metadata(metadata)
        
        # Set as active workspace
        await self.set_active_workspace(workspace_name)
        
        # Sync IDE settings if enabled
        if self.config.workspace.sync_ide_settings:
            await self._sync_ide_settings(repo_path, worktree_path, metadata)
        
        return metadata
    
    async def list_workspaces(self) -> WorkspaceList:
        """List all workspaces."""
        workspaces = []
        
        # Scan metadata directory for workspace files
        if self.metadata_dir.exists():
            for metadata_file in self.metadata_dir.glob("*.json"):
                if metadata_file.name != "config.json":
                    metadata = await self._load_workspace_metadata(metadata_file)
                    if metadata:
                        # Update status from git
                        try:
                            git_info = await self.git_manager.get_workspace_status(metadata.path)
                            metadata.git = git_info
                        except:
                            # Workspace might be stale
                            pass
                        workspaces.append(metadata)
        
        # Sort by creation time (newest first)
        workspaces.sort(key=lambda w: w.created_at, reverse=True)
        
        # Get active workspace
        active_workspace = await self.get_active_workspace_name()
        
        return WorkspaceList(
            workspaces=workspaces,
            active_workspace=active_workspace
        )
    
    async def get_workspace(self, name: str) -> Optional[WorkspaceMetadata]:
        """Get workspace by name."""
        metadata_file = self.metadata_dir / f"{name}.json"
        if not metadata_file.exists():
            return None
        
        return await self._load_workspace_metadata(metadata_file)
    
    async def set_active_workspace(self, name: str) -> None:
        """Set the active workspace."""
        # Verify workspace exists
        workspace = await self.get_workspace(name)
        if not workspace:
            raise ValueError(f"Workspace {name} not found")
        
        # Ensure parent directory exists
        self.active_workspace_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write active workspace file
        self.active_workspace_file.write_text(name)
    
    async def get_active_workspace_name(self) -> Optional[str]:
        """Get the active workspace name."""
        if not self.active_workspace_file.exists():
            return None
        
        name = self.active_workspace_file.read_text().strip()
        if not name:
            return None
        
        # Verify workspace still exists
        workspace = await self.get_workspace(name)
        if not workspace:
            # Clean up invalid active workspace
            self.active_workspace_file.unlink(missing_ok=True)
            return None
        
        return name
    
    async def get_active_workspace(self) -> Optional[WorkspaceMetadata]:
        """Get the active workspace metadata."""
        name = await self.get_active_workspace_name()
        if not name:
            return None
        
        return await self.get_workspace(name)
    
    async def update_workspace_metadata(self, metadata: WorkspaceMetadata) -> None:
        """Update workspace metadata."""
        metadata.update_timestamp()
        await self._save_workspace_metadata(metadata)
    
    async def delete_workspace(self, name: str) -> bool:
        """Delete a workspace and its worktree."""
        workspace = await self.get_workspace(name)
        if not workspace:
            return False
        
        # Get main repository
        repo = await self.git_manager.ensure_repository(workspace.main_repo_path)
        
        # Remove worktree
        success = await self.git_manager.remove_worktree(repo, workspace.path)
        
        # Remove metadata file
        metadata_file = self.metadata_dir / f"{name}.json"
        if metadata_file.exists():
            metadata_file.unlink()
        
        # Remove from active workspace if it's currently active
        active_name = await self.get_active_workspace_name()
        if active_name == name:
            self.active_workspace_file.unlink(missing_ok=True)
        
        return success
    
    async def cleanup_old_workspaces(self, days: int = None) -> List[str]:
        """Clean up old workspaces."""
        if days is None:
            days = self.config.workspace.auto_cleanup_days
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_workspaces = []
        
        workspaces = await self.list_workspaces()
        for workspace in workspaces.workspaces:
            # Only clean up completed or abandoned workspaces
            if workspace.status in [WorkspaceStatus.COMPLETED, WorkspaceStatus.ABANDONED]:
                if workspace.created_at < cutoff_date:
                    if await self.delete_workspace(workspace.name):
                        cleaned_workspaces.append(workspace.name)
        
        return cleaned_workspaces
    
    async def sync_workspace(
        self, 
        name: str, 
        strategy: str = "rebase"
    ) -> tuple[int, int, bool]:
        """Sync workspace with base branch."""
        workspace = await self.get_workspace(name)
        if not workspace:
            raise ValueError(f"Workspace {name} not found")
        
        return await self.git_manager.sync_worktree_with_base(
            workspace.path, 
            workspace.git.base_branch, 
            strategy
        )
    
    def _generate_workspace_name(self, issue_id: str, description: str) -> str:
        """Generate a workspace name from issue ID and description."""
        # Clean up description for use in filename
        clean_description = description.lower().replace(' ', '-')
        # Remove non-alphanumeric characters except hyphens
        clean_description = ''.join(c for c in clean_description if c.isalnum() or c == '-')
        # Limit length
        clean_description = clean_description[:30]
        
        # Combine issue ID and description
        return f"{issue_id.lower()}-{clean_description}"
    
    async def _save_workspace_metadata(self, metadata: WorkspaceMetadata) -> None:
        """Save workspace metadata to file."""
        # Ensure metadata directory exists
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = self.metadata_dir / f"{metadata.name}.json"
        
        # Convert to dict for JSON serialization
        metadata_dict = metadata.model_dump(mode='json')
        
        # Write to file
        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2, default=str)
    
    async def _load_workspace_metadata(self, metadata_file: Path) -> Optional[WorkspaceMetadata]:
        """Load workspace metadata from file."""
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
            
            # Convert path objects back to Path instances
            metadata_dict['path'] = Path(metadata_dict['path'])
            metadata_dict['main_repo_path'] = Path(metadata_dict['main_repo_path'])
            metadata_dict['git']['worktree_path'] = Path(metadata_dict['git']['worktree_path'])
            
            return WorkspaceMetadata.model_validate(metadata_dict)
        except (json.JSONDecodeError, Exception):
            # If metadata is corrupted, return None
            return None
    
    async def _sync_ide_settings(
        self, 
        repo_path: Path, 
        worktree_path: Path, 
        metadata: WorkspaceMetadata
    ) -> None:
        """Sync IDE settings from main repo to worktree."""
        copied_configs = []
        
        for config_dir in self.config.workspace.ide_config_dirs:
            source_dir = repo_path / config_dir
            target_dir = worktree_path / config_dir
            
            if source_dir.exists() and source_dir.is_dir():
                try:
                    # Copy the entire configuration directory
                    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
                    copied_configs.append(config_dir)
                except Exception:
                    # If copy fails, continue with other configs
                    pass
        
        # Update metadata
        metadata.settings_synced = True
        metadata.ide_configs_copied = copied_configs
        await self._save_workspace_metadata(metadata)