"""Git worktree operations manager for feature development."""

import asyncio
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

import git
from git import Repo, GitCommandError

from ..config import FeatureWorkflowConfig
from ..models.workspace import WorkspaceMetadata, GitInfo


class WorktreeManager:
    """Manages git worktree operations for feature development."""
    
    def __init__(self, config: FeatureWorkflowConfig):
        self.config = config
    
    async def create_worktree(
        self,
        repo: Repo,
        branch_name: str,
        worktree_name: str,
        base_branch: str = "main"
    ) -> Path:
        """Create a new git worktree for feature development."""
        try:
            # Get worktree directory
            repo_path = Path(repo.working_dir)
            worktrees_dir = self.config.get_worktree_dir(repo_path)
            worktree_path = worktrees_dir / worktree_name
            
            # Check if worktree already exists
            if worktree_path.exists():
                raise ValueError(f"Worktree {worktree_name} already exists")
            
            # Create new branch if it doesn't exist
            if branch_name not in [branch.name for branch in repo.branches]:
                # Ensure we're up to date with remote
                if f"origin/{base_branch}" in [ref.name for ref in repo.refs]:
                    repo.git.fetch("origin", base_branch)
                    base_ref = f"origin/{base_branch}"
                else:
                    base_ref = base_branch
                
                # Create worktree with new branch
                repo.git.worktree("add", "-b", branch_name, str(worktree_path), base_ref)
            else:
                # Create worktree from existing branch
                repo.git.worktree("add", str(worktree_path), branch_name)
            
            return worktree_path
            
        except GitCommandError as e:
            raise ValueError(f"Failed to create worktree: {e}")
    
    async def remove_worktree(self, repo: Repo, worktree_path: Path) -> bool:
        """Remove a git worktree."""
        try:
            if not worktree_path.exists():
                return False
            
            # Remove worktree from git
            repo.git.worktree("remove", str(worktree_path), "--force")
            
            # Clean up any remaining directory
            if worktree_path.exists():
                shutil.rmtree(worktree_path)
            
            return True
            
        except GitCommandError as e:
            # If git command fails, try manual cleanup
            if worktree_path.exists():
                shutil.rmtree(worktree_path)
            return True
    
    async def list_worktrees(self, repo: Repo) -> List[Tuple[Path, str, bool]]:
        """List all git worktrees for the repository."""
        try:
            # Get worktree list from git
            worktree_output = repo.git.worktree("list", "--porcelain")
            
            worktrees = []
            current_worktree = {}
            
            for line in worktree_output.split('\n'):
                if line.startswith('worktree '):
                    if current_worktree:
                        worktrees.append(self._parse_worktree_info(current_worktree))
                    current_worktree = {'path': line.split(' ', 1)[1]}
                elif line.startswith('HEAD '):
                    current_worktree['head'] = line.split(' ', 1)[1]
                elif line.startswith('branch '):
                    current_worktree['branch'] = line.split(' ', 1)[1]
                elif line == 'bare':
                    current_worktree['bare'] = True
                elif line == 'detached':
                    current_worktree['detached'] = True
            
            # Don't forget the last worktree
            if current_worktree:
                worktrees.append(self._parse_worktree_info(current_worktree))
            
            return worktrees
            
        except GitCommandError:
            return []
    
    async def prune_worktrees(self, repo: Repo) -> List[str]:
        """Prune stale worktree references."""
        try:
            # Prune stale worktree references
            result = repo.git.worktree("prune", "--verbose")
            
            # Parse the output to get pruned worktrees
            pruned = []
            for line in result.split('\n'):
                if line.strip():
                    pruned.append(line.strip())
            
            return pruned
            
        except GitCommandError:
            return []
    
    async def get_worktree_status(self, worktree_path: Path) -> GitInfo:
        """Get git status for a specific worktree."""
        try:
            worktree_repo = Repo(worktree_path)
            
            # Get basic info
            current_branch = worktree_repo.active_branch.name
            
            # Get remote info
            remote_url = ""
            if worktree_repo.remotes:
                remote_url = worktree_repo.remotes[0].url
            
            # Get file status
            modified_files = len([item.a_path for item in worktree_repo.index.diff(None)])
            staged_files = len([item.a_path for item in worktree_repo.index.diff("HEAD")])
            
            # Get commits ahead/behind base branch
            commits_ahead = 0
            commits_behind = 0
            
            try:
                base_branch = self.config.git.default_base_branch
                if f"origin/{base_branch}" in [ref.name for ref in worktree_repo.refs]:
                    ahead_behind = worktree_repo.git.rev_list(
                        "--left-right", "--count", 
                        f"origin/{base_branch}...{current_branch}"
                    ).split('\t')
                    commits_behind = int(ahead_behind[0])
                    commits_ahead = int(ahead_behind[1])
            except:
                pass
            
            return GitInfo(
                repo_url=remote_url,
                base_branch=self.config.git.default_base_branch,
                branch_name=current_branch,
                worktree_path=worktree_path,
                is_worktree=True,
                commits_ahead=commits_ahead,
                commits_behind=commits_behind,
                modified_files=modified_files,
                staged_files=staged_files
            )
            
        except Exception as e:
            raise ValueError(f"Failed to get worktree status: {e}")
    
    async def sync_worktree_with_base(
        self, 
        worktree_path: Path, 
        base_branch: str = "main",
        strategy: str = "rebase"
    ) -> Tuple[int, int, bool]:
        """Sync worktree with base branch."""
        try:
            worktree_repo = Repo(worktree_path)
            
            # Fetch latest changes
            worktree_repo.remote('origin').fetch()
            
            # Get current state
            current_branch = worktree_repo.active_branch.name
            
            # Count commits before sync
            ahead_behind_before = worktree_repo.git.rev_list(
                "--left-right", "--count", 
                f"origin/{base_branch}...{current_branch}"
            ).split('\t')
            commits_behind_before = int(ahead_behind_before[0])
            commits_ahead_before = int(ahead_behind_before[1])
            
            # Perform sync based on strategy
            has_conflicts = False
            if strategy == "rebase":
                try:
                    worktree_repo.git.rebase(f"origin/{base_branch}")
                except GitCommandError as e:
                    if "conflict" in str(e).lower():
                        has_conflicts = True
                    else:
                        raise
            else:  # merge
                try:
                    worktree_repo.git.merge(f"origin/{base_branch}")
                except GitCommandError as e:
                    if "conflict" in str(e).lower():
                        has_conflicts = True
                    else:
                        raise
            
            # Get new state (only if no conflicts)
            commits_ahead_after = commits_ahead_before
            commits_behind_after = 0
            
            if not has_conflicts:
                ahead_behind_after = worktree_repo.git.rev_list(
                    "--left-right", "--count", 
                    f"origin/{base_branch}...{current_branch}"
                ).split('\t')
                commits_behind_after = int(ahead_behind_after[0])
                commits_ahead_after = int(ahead_behind_after[1])
            
            return commits_ahead_after, commits_behind_after, has_conflicts
            
        except Exception as e:
            raise ValueError(f"Failed to sync worktree: {e}")
    
    def _parse_worktree_info(self, worktree_data: dict) -> Tuple[Path, str, bool]:
        """Parse worktree information from git worktree list output."""
        path = Path(worktree_data['path'])
        branch = worktree_data.get('branch', 'HEAD')
        is_main = 'bare' in worktree_data or branch == 'refs/heads/main'
        
        # Clean up branch name
        if branch.startswith('refs/heads/'):
            branch = branch[11:]  # Remove 'refs/heads/' prefix
        
        return path, branch, is_main
    
    async def is_worktree(self, path: Path) -> bool:
        """Check if a directory is a git worktree."""
        try:
            repo = Repo(path)
            git_dir = Path(repo.git_dir)
            
            # Worktrees have a .git file pointing to the worktree, not a .git directory
            git_file = path / ".git"
            return git_file.is_file() and "worktrees" in git_file.read_text()
        except:
            return False