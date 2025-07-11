"""Main MCP server for feature workflow automation."""

import asyncio
import json
from typing import Any, Dict, List, Optional

from .config import config
from .managers.workspace_manager import WorkspaceManager
from .managers.git_manager import GitManager
from .models.workspace import WorkspaceMetadata


class FeatureWorkflowServer:
    """MCP server for feature workflow automation."""
    
    def __init__(self):
        self.config = config
        self.workspace_manager = WorkspaceManager(config)
        self.git_manager = GitManager(config)
    
    async def start_feature(
        self,
        issue_id: str,
        description: str,
        base_branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start a new feature workspace using git worktrees."""
        try:
            # Validate inputs
            if not issue_id or not description:
                raise ValueError("Issue ID and description are required")
            
            # Use default base branch if not provided
            if not base_branch:
                base_branch = self.config.git.default_base_branch
            
            # Create worktree-based workspace
            workspace = await self.workspace_manager.create_workspace(
                issue_id=issue_id,
                description=description,
                base_branch=base_branch
            )
            
            return {
                "success": True,
                "workspace_path": str(workspace.path),
                "branch_name": workspace.branch_name,
                "issue_id": workspace.issue_id,
                "description": workspace.description,
                "main_repo_path": str(workspace.main_repo_path),
                "settings_synced": workspace.settings_synced,
                "ide_configs_copied": workspace.ide_configs_copied
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_features(self) -> Dict[str, Any]:
        """List all feature workspaces."""
        try:
            workspace_list = await self.workspace_manager.list_workspaces()
            
            workspaces_data = []
            for workspace in workspace_list.workspaces:
                workspaces_data.append({
                    "name": workspace.name,
                    "path": str(workspace.path),
                    "branch": workspace.branch_name,
                    "issue_id": workspace.issue_id,
                    "description": workspace.description,
                    "commits_ahead": workspace.git.commits_ahead,
                    "commits_behind": workspace.git.commits_behind,
                    "modified_files": workspace.git.modified_files,
                    "staged_files": workspace.git.staged_files,
                    "last_commit": workspace.updated_at.isoformat(),
                    "is_active": workspace.name == workspace_list.active_workspace,
                    "status": workspace.status.value,
                    "is_worktree": workspace.git.is_worktree,
                    "main_repo_path": str(workspace.main_repo_path),
                    "settings_synced": workspace.settings_synced
                })
            
            return {
                "success": True,
                "workspaces": workspaces_data,
                "active_workspace": workspace_list.active_workspace
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def switch_feature(self, workspace_name: str) -> Dict[str, Any]:
        """Switch to a different feature workspace."""
        try:
            # Validate workspace exists
            workspace = await self.workspace_manager.get_workspace(workspace_name)
            if not workspace:
                raise ValueError(f"Workspace '{workspace_name}' not found")
            
            # Set as active workspace
            await self.workspace_manager.set_active_workspace(workspace_name)
            
            return {
                "success": True,
                "workspace_name": workspace_name,
                "workspace_path": str(workspace.path),
                "branch_name": workspace.branch_name,
                "issue_id": workspace.issue_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def commit_feature(
        self,
        message: str,
        close_issue: bool = False
    ) -> Dict[str, Any]:
        """Commit changes in the active workspace."""
        try:
            # Get active workspace
            workspace = await self.workspace_manager.get_active_workspace()
            if not workspace:
                raise ValueError("No active workspace found")
            
            # Validate git repository
            if not await self.git_manager.is_git_repository(workspace.path):
                raise ValueError("Active workspace is not a git repository")
            
            # Load git repository
            from git import Repo
            repo = Repo(workspace.path)
            
            # Commit changes
            commit_hash = await self.git_manager.commit_changes(
                repo=repo,
                message=message,
                issue_id=workspace.issue_id,
                is_closing=close_issue
            )
            
            # Update workspace metadata
            workspace.add_commit(commit_hash)
            await self.workspace_manager.update_workspace_metadata(workspace)
            
            return {
                "success": True,
                "commit_hash": commit_hash,
                "workspace_name": workspace.name,
                "issue_id": workspace.issue_id,
                "message": message,
                "closes_issue": close_issue
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def feature_status(self) -> Dict[str, Any]:
        """Get detailed status of the current feature."""
        try:
            # Get active workspace
            workspace = await self.workspace_manager.get_active_workspace()
            if not workspace:
                raise ValueError("No active workspace found")
            
            # Get current git status
            if await self.git_manager.is_git_repository(workspace.path):
                git_info = await self.git_manager.get_workspace_status(workspace.path)
            else:
                git_info = workspace.git
            
            return {
                "success": True,
                "workspace": workspace.name,
                "branch": workspace.branch_name,
                "issue": {
                    "id": workspace.issue_id,
                    "title": workspace.issue.title,
                    "description": workspace.issue.description
                },
                "git": {
                    "commits_ahead": git_info.commits_ahead,
                    "commits_behind": git_info.commits_behind,
                    "modified_files": git_info.modified_files,
                    "staged_files": git_info.staged_files,
                    "repo_url": git_info.repo_url,
                    "base_branch": git_info.base_branch
                },
                "workspace_path": str(workspace.path),
                "created_at": workspace.created_at.isoformat(),
                "updated_at": workspace.updated_at.isoformat(),
                "status": workspace.status.value
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_features(
        self,
        older_than_days: int = 7,
        completed_only: bool = True
    ) -> Dict[str, Any]:
        """Clean up old workspaces."""
        try:
            cleaned_workspaces = await self.workspace_manager.cleanup_old_workspaces(
                days=older_than_days
            )
            
            return {
                "success": True,
                "cleaned_workspaces": cleaned_workspaces,
                "count": len(cleaned_workspaces)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }