"""Workspace management for feature development."""

import asyncio
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from ..config import FeatureWorkflowConfig
from ..models.workspace import WorkspaceMetadata, WorkspaceList, WorkspaceStatus, LinearIssue, GitInfo


class WorkspaceManager:
    """Manages isolated feature development workspaces."""
    
    def __init__(self, config: FeatureWorkflowConfig):
        self.config = config
        self.base_dir = config.workspace_base_dir
        self.active_workspace_file = config.active_workspace_file
    
    async def create_workspace(
        self,
        issue_id: str,
        description: str,
        repo_url: str,
        base_branch: str = "main"
    ) -> WorkspaceMetadata:
        """Create a new feature workspace."""
        # Generate workspace name
        workspace_name = self._generate_workspace_name(issue_id, description)
        workspace_path = self.base_dir / workspace_name
        
        # Check if workspace already exists
        if workspace_path.exists():
            raise ValueError(f"Workspace {workspace_name} already exists")
        
        # Check workspace limit
        existing_workspaces = await self.list_workspaces()
        if len(existing_workspaces.workspaces) >= self.config.workspace.max_workspaces:
            raise ValueError(f"Maximum number of workspaces ({self.config.workspace.max_workspaces}) reached")
        
        # Create workspace directory
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Generate branch name
        branch_name = f"feature/{workspace_name}"
        
        # Create workspace metadata
        linear_issue = LinearIssue(id=issue_id, title=description)
        git_info = GitInfo(
            repo_url=repo_url,
            base_branch=base_branch,
            branch_name=branch_name
        )
        
        metadata = WorkspaceMetadata(
            name=workspace_name,
            path=workspace_path,
            description=description,
            issue=linear_issue,
            git=git_info
        )
        
        # Save metadata
        await self._save_workspace_metadata(metadata)
        
        # Set as active workspace
        await self.set_active_workspace(workspace_name)
        
        return metadata
    
    async def list_workspaces(self) -> WorkspaceList:
        """List all workspaces."""
        workspaces = []
        
        if not self.base_dir.exists():
            return WorkspaceList(workspaces=workspaces)
        
        for workspace_path in self.base_dir.iterdir():
            if workspace_path.is_dir() and not workspace_path.name.startswith('.'):
                metadata = await self._load_workspace_metadata(workspace_path)
                if metadata:
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
        workspace_path = self.base_dir / name
        if not workspace_path.exists():
            return None
        
        return await self._load_workspace_metadata(workspace_path)
    
    async def set_active_workspace(self, name: str) -> None:
        """Set the active workspace."""
        # Verify workspace exists
        workspace = await self.get_workspace(name)
        if not workspace:
            raise ValueError(f"Workspace {name} not found")
        
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
        """Delete a workspace."""
        workspace_path = self.base_dir / name
        if not workspace_path.exists():
            return False
        
        # Remove from active workspace if it's currently active
        active_name = await self.get_active_workspace_name()
        if active_name == name:
            self.active_workspace_file.unlink(missing_ok=True)
        
        # Remove workspace directory
        shutil.rmtree(workspace_path)
        
        return True
    
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
        metadata_file = metadata.path / ".feature-metadata.json"
        
        # Convert to dict for JSON serialization
        metadata_dict = metadata.model_dump(mode='json')
        
        # Write to file
        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2, default=str)
    
    async def _load_workspace_metadata(self, workspace_path: Path) -> Optional[WorkspaceMetadata]:
        """Load workspace metadata from file."""
        metadata_file = workspace_path / ".feature-metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
            
            # Convert path back to Path object
            metadata_dict['path'] = Path(metadata_dict['path'])
            
            return WorkspaceMetadata.model_validate(metadata_dict)
        except (json.JSONDecodeError, Exception):
            # If metadata is corrupted, return None
            return None