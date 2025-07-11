"""Unit tests for GitManager."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from feature_workflow.managers.git_manager import GitManager


class TestGitManager:
    """Test cases for GitManager."""
    
    def test_format_commit_message(self, test_config):
        """Test commit message formatting."""
        manager = GitManager(test_config)
        
        # Test regular commit
        message = manager._format_commit_message(
            "Add user authentication",
            "AIM-123",
            is_closing=False
        )
        
        assert "Add user authentication" in message
        assert "Part of AIM-123" in message
        assert "🤖 Generated with [Claude Code]" in message
        assert "Co-Authored-By: Claude" in message
        
        # Test closing commit
        message = manager._format_commit_message(
            "Fix authentication bug",
            "AIM-124",
            is_closing=True
        )
        
        assert "Fix authentication bug" in message
        assert "Fixes AIM-124" in message
        assert "🤖 Generated with [Claude Code]" in message
    
    @pytest.mark.asyncio
    async def test_validate_repository_url(self, test_config):
        """Test repository URL validation."""
        manager = GitManager(test_config)
        
        # Valid URLs
        valid_urls = [
            "https://github.com/user/repo.git",
            "https://github.com/user/repo",
            "git@github.com:user/repo.git",
            "ssh://git@github.com/user/repo.git",
            "https://gitlab.com/user/repo.git",
        ]
        
        for url in valid_urls:
            assert await manager.validate_repository_url(url), f"URL should be valid: {url}"
        
        # Invalid URLs
        invalid_urls = [
            "not-a-url",
            "ftp://example.com/repo",
            "https://",
            "",
            "github.com/user/repo",  # Missing protocol
        ]
        
        for url in invalid_urls:
            assert not await manager.validate_repository_url(url), f"URL should be invalid: {url}"
    
    @pytest.mark.asyncio
    @patch('feature_workflow.managers.git_manager.Repo')
    async def test_clone_repository(self, mock_repo_class, test_config, temp_workspace_dir):
        """Test repository cloning."""
        manager = GitManager(test_config)
        
        # Mock repository
        mock_repo = Mock()
        mock_config_writer = Mock()
        mock_repo.config_writer.return_value.__enter__.return_value = mock_config_writer
        mock_repo_class.clone_from.return_value = mock_repo
        
        # Test cloning
        repo = await manager.clone_repository(
            "https://github.com/test/repo.git",
            temp_workspace_dir / "test-workspace"
        )
        
        # Verify clone was called
        mock_repo_class.clone_from.assert_called_once_with(
            "https://github.com/test/repo.git",
            temp_workspace_dir / "test-workspace",
            branch="main"
        )
        
        # Verify git config was set
        mock_config_writer.set_value.assert_any_call("user", "name", test_config.git.user_name)
        mock_config_writer.set_value.assert_any_call("user", "email", test_config.git.user_email)
        
        assert repo == mock_repo
    
    @pytest.mark.asyncio
    @patch('feature_workflow.managers.git_manager.Repo')
    async def test_create_feature_branch(self, mock_repo_class, test_config):
        """Test feature branch creation."""
        manager = GitManager(test_config)
        
        # Mock repository and branches
        mock_repo = Mock()
        mock_base_branch = Mock()
        mock_feature_branch = Mock()
        
        mock_repo.heads = {'main': mock_base_branch}
        mock_repo.create_head.return_value = mock_feature_branch
        
        # Test branch creation
        await manager.create_feature_branch(
            repo=mock_repo,
            branch_name="feature/test-branch",
            base_branch="main"
        )
        
        # Verify checkout and branch creation
        mock_base_branch.checkout.assert_called_once()
        mock_repo.create_head.assert_called_once_with("feature/test-branch")
        mock_feature_branch.checkout.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('feature_workflow.managers.git_manager.Repo')
    async def test_commit_changes(self, mock_repo_class, test_config):
        """Test committing changes."""
        manager = GitManager(test_config)
        
        # Mock repository
        mock_repo = Mock()
        mock_commit = Mock()
        mock_commit.hexsha = "abc123"
        
        mock_repo.index.diff.return_value = [Mock()]  # Has changes
        mock_repo.index.commit.return_value = mock_commit
        
        # Test commit
        commit_hash = await manager.commit_changes(
            repo=mock_repo,
            message="Test commit",
            issue_id="AIM-123",
            is_closing=False
        )
        
        # Verify staging and commit
        mock_repo.git.add.assert_called_once_with(A=True)
        mock_repo.index.commit.assert_called_once()
        
        # Verify commit message format
        call_args = mock_repo.index.commit.call_args
        commit_message = call_args[0][0]
        assert "Test commit" in commit_message
        assert "Part of AIM-123" in commit_message
        
        assert commit_hash == "abc123"
    
    @pytest.mark.asyncio
    @patch('feature_workflow.managers.git_manager.Repo')
    async def test_commit_no_changes(self, mock_repo_class, test_config):
        """Test committing when there are no changes."""
        manager = GitManager(test_config)
        
        # Mock repository with no changes
        mock_repo = Mock()
        mock_repo.index.diff.return_value = []  # No changes
        
        # Test commit should raise error
        with pytest.raises(ValueError, match="No changes to commit"):
            await manager.commit_changes(
                repo=mock_repo,
                message="Test commit",
                issue_id="AIM-123"
            )
    
    @pytest.mark.asyncio
    @patch('feature_workflow.managers.git_manager.Repo')
    async def test_is_git_repository(self, mock_repo_class, test_config, temp_workspace_dir):
        """Test git repository detection."""
        manager = GitManager(test_config)
        
        # Mock successful repo creation
        mock_repo_class.return_value = Mock()
        
        # Test valid repo
        is_repo = await manager.is_git_repository(temp_workspace_dir)
        assert is_repo
        
        # Mock repo creation failure
        mock_repo_class.side_effect = Exception("Not a git repo")
        
        # Test invalid repo
        is_repo = await manager.is_git_repository(temp_workspace_dir)
        assert not is_repo