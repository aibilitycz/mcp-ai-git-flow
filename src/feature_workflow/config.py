"""Configuration management for feature workflow MCP server."""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkspaceConfig(BaseModel):
    """Configuration for git worktree-based workspace management."""
    
    worktrees_dir: str = Field(
        default="worktrees",
        description="Directory name for worktrees (relative to repo root)"
    )
    max_worktrees: int = Field(
        default=10,
        description="Maximum number of concurrent worktrees"
    )
    auto_cleanup_days: int = Field(
        default=7,
        description="Auto-cleanup worktrees older than N days"
    )
    sync_ide_settings: bool = Field(
        default=True,
        description="Automatically sync IDE settings to worktrees"
    )
    ide_config_dirs: list[str] = Field(
        default=[".vscode", ".cursor", ".idea"],
        description="IDE configuration directories to sync"
    )


class GitConfig(BaseModel):
    """Configuration for git operations."""
    
    default_base_branch: str = Field(
        default="main",
        description="Default base branch for new features"
    )
    user_name: str = Field(
        default="Claude Code",
        description="Git commit author name"
    )
    user_email: str = Field(
        default="claude@anthropic.com",
        description="Git commit author email"
    )


class LinearConfig(BaseModel):
    """Configuration for Linear integration via commit messages."""
    
    issue_prefix: str = Field(
        default="AIM",
        description="Linear issue prefix (e.g., AIM-123)"
    )
    close_keywords: list[str] = Field(
        default=["Fixes", "Closes", "Resolves"],
        description="Keywords that close Linear issues"
    )
    reference_keywords: list[str] = Field(
        default=["Part of", "Related to", "Refs"],
        description="Keywords that reference Linear issues"
    )


class GitHubConfig(BaseModel):
    """Configuration for GitHub integration."""
    
    token: Optional[str] = Field(
        default=None,
        description="GitHub API token"
    )
    repo: Optional[str] = Field(
        default=None,
        description="GitHub repository (owner/repo)"
    )


class GitLabConfig(BaseModel):
    """Configuration for GitLab integration."""
    
    token: Optional[str] = Field(
        default=None,
        description="GitLab API token"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="GitLab project ID"
    )


class FeatureWorkflowConfig(BaseSettings):
    """Main configuration for feature workflow MCP server."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="FEATURE_WORKFLOW_",
        case_sensitive=False,
    )
    
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    linear: LinearConfig = Field(default_factory=LinearConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    gitlab: GitLabConfig = Field(default_factory=GitLabConfig)
    
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    @property
    def active_workspace_file(self) -> Path:
        """Get the active workspace tracking file (stored in current repo)."""
        return Path.cwd() / ".feature-workflow" / "active-workspace"
    
    @property
    def worktrees_metadata_dir(self) -> Path:
        """Get the worktrees metadata directory."""
        metadata_dir = Path.cwd() / ".feature-workflow"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        return metadata_dir
    
    @property
    def workspace_base_dir(self) -> Path:
        """Get the base directory for all workspaces."""
        return Path.cwd() / self.workspace.worktrees_dir
    
    def get_worktree_dir(self, repo_path: Path) -> Path:
        """Get the worktrees directory for a given repository."""
        worktree_dir = repo_path / self.workspace.worktrees_dir
        worktree_dir.mkdir(parents=True, exist_ok=True)
        return worktree_dir


# Global configuration instance
config = FeatureWorkflowConfig()