"""Git operations manager for feature development with worktree support."""

import asyncio
import re
from pathlib import Path
from typing import List, Optional, Tuple

import git
from git import Repo, GitCommandError

from ..config import FeatureWorkflowConfig
from ..models.workspace import WorkspaceMetadata, GitInfo
from .worktree_manager import WorktreeManager


class GitManager:
    """Manages git operations for feature workspaces using worktrees."""
    
    def __init__(self, config: FeatureWorkflowConfig):
        self.config = config
        self.worktree_manager = WorktreeManager(config)
    
    async def ensure_repository(self, repo_path: Path = None) -> Repo:
        """Ensure we have a git repository to work with."""
        if repo_path is None:
            repo_path = Path.cwd()
        
        try:
            repo = Repo(repo_path)
            
            # Configure git user if not set
            try:
                repo.config_reader().get_value("user", "name")
            except:
                with repo.config_writer() as git_config:
                    git_config.set_value("user", "name", self.config.git.user_name)
                    git_config.set_value("user", "email", self.config.git.user_email)
            
            return repo
        except git.InvalidGitRepositoryError:
            raise ValueError(f"No git repository found at {repo_path}")
    
    async def create_worktree_for_feature(
        self,
        repo: Repo,
        feature_name: str,
        branch_name: str,
        base_branch: str = "main"
    ) -> Path:
        """Create a git worktree for feature development."""
        return await self.worktree_manager.create_worktree(
            repo=repo,
            branch_name=branch_name,
            worktree_name=feature_name,
            base_branch=base_branch
        )
    
    async def create_feature_branch(self, repo: Repo, branch_name: str, base_branch: str = "main") -> None:
        """Create and checkout feature branch."""
        try:
            # Ensure we're on the base branch
            if base_branch in repo.heads:
                repo.heads[base_branch].checkout()
            else:
                # If base branch doesn't exist locally, create it from origin
                if f"origin/{base_branch}" in [ref.name for ref in repo.refs]:
                    repo.create_head(base_branch, f"origin/{base_branch}")
                    repo.heads[base_branch].checkout()
                else:
                    raise ValueError(f"Base branch '{base_branch}' not found")
            
            # Create feature branch
            feature_branch = repo.create_head(branch_name)
            feature_branch.checkout()
            
        except GitCommandError as e:
            raise ValueError(f"Failed to create feature branch: {e}")
    
    async def commit_changes(
        self,
        repo: Repo,
        message: str,
        issue_id: str,
        is_closing: bool = False
    ) -> str:
        """Commit changes with Linear issue reference."""
        try:
            # Stage all changes
            repo.git.add(A=True)
            
            # Check if there are changes to commit
            if not repo.index.diff("HEAD"):
                raise ValueError("No changes to commit")
            
            # Format commit message with Linear integration
            formatted_message = self._format_commit_message(message, issue_id, is_closing)
            
            # Create commit
            commit = repo.index.commit(formatted_message)
            
            return commit.hexsha
            
        except GitCommandError as e:
            raise ValueError(f"Failed to commit changes: {e}")
    
    async def push_branch(self, repo: Repo, branch_name: str) -> None:
        """Push branch to remote."""
        try:
            origin = repo.remote('origin')
            origin.push(branch_name)
        except GitCommandError as e:
            raise ValueError(f"Failed to push branch: {e}")
    
    async def sync_with_base(self, repo: Repo, base_branch: str = "main") -> Tuple[int, int]:
        """Sync feature branch with base branch."""
        try:
            # Fetch latest changes
            repo.remote('origin').fetch()
            
            # Get current branch
            current_branch = repo.active_branch.name
            
            # Get commits ahead and behind
            commits_ahead = list(repo.iter_commits(f"origin/{base_branch}..{current_branch}"))
            commits_behind = list(repo.iter_commits(f"{current_branch}..origin/{base_branch}"))
            
            return len(commits_ahead), len(commits_behind)
            
        except GitCommandError as e:
            raise ValueError(f"Failed to sync with base branch: {e}")
    
    async def get_workspace_status(self, workspace_path: Path) -> GitInfo:
        """Get git status for workspace (worktree-aware)."""
        return await self.worktree_manager.get_worktree_status(workspace_path)
    
    async def list_worktrees(self, repo: Repo) -> List[Tuple[Path, str, bool]]:
        """List all worktrees for the repository."""
        return await self.worktree_manager.list_worktrees(repo)
    
    async def remove_worktree(self, repo: Repo, worktree_path: Path) -> bool:
        """Remove a worktree."""
        return await self.worktree_manager.remove_worktree(repo, worktree_path)
    
    async def sync_worktree_with_base(
        self, 
        worktree_path: Path, 
        base_branch: str = "main",
        strategy: str = "rebase"
    ) -> Tuple[int, int, bool]:
        """Sync worktree with base branch."""
        return await self.worktree_manager.sync_worktree_with_base(
            worktree_path, base_branch, strategy
        )
    
    async def is_git_repository(self, path: Path) -> bool:
        """Check if path is a git repository."""
        try:
            Repo(path)
            return True
        except:
            return False
    
    def _format_commit_message(self, message: str, issue_id: str, is_closing: bool = False) -> str:
        """Format commit message with Linear issue reference."""
        # Choose keyword based on whether this closes the issue
        if is_closing:
            keyword = "Fixes"
        else:
            keyword = "Part of"
        
        # Build commit message
        formatted_message = f"{message}\n\n{keyword} {issue_id}"
        
        # Add Claude Code signature
        formatted_message += f"\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        
        return formatted_message
    
    async def validate_repository_url(self, repo_url: str) -> bool:
        """Validate repository URL format."""
        # Basic validation for common git URL formats
        git_url_pattern = re.compile(
            r'^(https?://|git@|ssh://)'
            r'[a-zA-Z0-9.-]+'
            r'[:/]'
            r'[a-zA-Z0-9._-]+/'
            r'[a-zA-Z0-9._-]+'
            r'(\.git)?/?$'
        )
        
        return bool(git_url_pattern.match(repo_url))
    
    async def get_default_branch(self, repo: Repo) -> str:
        """Get the default branch for the repository."""
        try:
            # Try to get default branch from remote
            origin = repo.remote('origin')
            origin.fetch()
            
            # Look for main, master, or develop
            for branch_name in ['main', 'master', 'develop']:
                if f"origin/{branch_name}" in [ref.name for ref in repo.refs]:
                    return branch_name
            
            # If none found, use the first remote branch
            remote_branches = [ref.name.split('/')[-1] for ref in repo.refs if ref.name.startswith('origin/')]
            if remote_branches:
                return remote_branches[0]
            
            return self.config.git.default_base_branch
            
        except:
            return self.config.git.default_base_branch