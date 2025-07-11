"""Pydantic models for workspace metadata and management."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, validator


class WorkspaceStatus(str, Enum):
    """Status of a feature workspace."""
    
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class LinearIssue(BaseModel):
    """Linear issue information."""
    
    id: str = Field(..., description="Linear issue ID (e.g., AIM-123)")
    title: Optional[str] = Field(None, description="Issue title")
    description: Optional[str] = Field(None, description="Issue description")
    
    @validator("id")
    def validate_issue_id(cls, v):
        """Validate Linear issue ID format."""
        if not v.upper().startswith(("AIM-", "FEAT-", "BUG-", "TASK-")):
            raise ValueError("Issue ID must start with AIM-, FEAT-, BUG-, or TASK-")
        return v.upper()


class GitInfo(BaseModel):
    """Git repository information for worktree-based development."""
    
    repo_url: str = Field(..., description="Repository URL")
    base_branch: str = Field(default="main", description="Base branch")
    branch_name: str = Field(..., description="Feature branch name")
    worktree_path: Path = Field(..., description="Path to git worktree")
    is_worktree: bool = Field(default=True, description="Whether this is a git worktree")
    commits_ahead: int = Field(default=0, description="Commits ahead of base")
    commits_behind: int = Field(default=0, description="Commits behind base")
    modified_files: int = Field(default=0, description="Number of modified files")
    staged_files: int = Field(default=0, description="Number of staged files")


class WorkspaceMetadata(BaseModel):
    """Metadata for a feature workspace using git worktrees."""
    
    version: str = Field(default="2.0", description="Metadata version (2.0 = worktree-based)")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    # Workspace info
    name: str = Field(..., description="Workspace name")
    path: Path = Field(..., description="Worktree path")
    description: str = Field(..., description="Feature description")
    status: WorkspaceStatus = Field(default=WorkspaceStatus.ACTIVE, description="Workspace status")
    
    # Linear integration
    issue: LinearIssue = Field(..., description="Associated Linear issue")
    
    # Git worktree info
    git: GitInfo = Field(..., description="Git worktree information")
    main_repo_path: Path = Field(..., description="Path to main repository")
    
    # Commit tracking
    commits: list[str] = Field(default_factory=list, description="List of commit hashes")
    
    # IDE integration
    settings_synced: bool = Field(default=False, description="Whether IDE settings have been synced")
    ide_configs_copied: list[str] = Field(default_factory=list, description="List of copied IDE config directories")
    
    def update_timestamp(self) -> None:
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()
    
    def add_commit(self, commit_hash: str) -> None:
        """Add a commit hash to the tracking list."""
        if commit_hash not in self.commits:
            self.commits.append(commit_hash)
            self.update_timestamp()
    
    @property
    def is_active(self) -> bool:
        """Check if workspace is active."""
        return self.status == WorkspaceStatus.ACTIVE
    
    @property
    def branch_name(self) -> str:
        """Get the git branch name."""
        return self.git.branch_name
    
    @property
    def issue_id(self) -> str:
        """Get the Linear issue ID."""
        return self.issue.id


class WorkspaceList(BaseModel):
    """List of workspaces with metadata."""
    
    workspaces: list[WorkspaceMetadata] = Field(default_factory=list)
    active_workspace: Optional[str] = Field(None, description="Currently active workspace name")
    
    def get_active_workspace(self) -> Optional[WorkspaceMetadata]:
        """Get the currently active workspace."""
        if not self.active_workspace:
            return None
        return next(
            (ws for ws in self.workspaces if ws.name == self.active_workspace),
            None
        )
    
    def get_workspace_by_name(self, name: str) -> Optional[WorkspaceMetadata]:
        """Get workspace by name."""
        return next(
            (ws for ws in self.workspaces if ws.name == name),
            None
        )
    
    def add_workspace(self, workspace: WorkspaceMetadata) -> None:
        """Add a workspace to the list."""
        # Remove existing workspace with same name
        self.workspaces = [ws for ws in self.workspaces if ws.name != workspace.name]
        self.workspaces.append(workspace)
    
    def remove_workspace(self, name: str) -> bool:
        """Remove a workspace by name."""
        original_count = len(self.workspaces)
        self.workspaces = [ws for ws in self.workspaces if ws.name != name]
        return len(self.workspaces) < original_count