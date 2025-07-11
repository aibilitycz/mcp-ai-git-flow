"""Test configuration and fixtures for feature workflow MCP server."""

import tempfile
from pathlib import Path
from typing import Generator
import pytest
from unittest.mock import Mock

from feature_workflow.config import FeatureWorkflowConfig
from feature_workflow.models.workspace import LinearIssue, GitInfo, WorkspaceMetadata


@pytest.fixture
def temp_workspace_dir() -> Generator[Path, None, None]:
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config(temp_workspace_dir: Path) -> FeatureWorkflowConfig:
    """Create a test configuration with temporary workspace directory."""
    config = FeatureWorkflowConfig()
    config.workspace.base_dir = temp_workspace_dir
    config.workspace.max_workspaces = 5
    config.workspace.auto_cleanup_days = 1
    config.git.default_base_branch = "main"
    config.linear.issue_prefix = "TEST"
    return config


@pytest.fixture
def sample_linear_issue() -> LinearIssue:
    """Create a sample Linear issue for testing."""
    return LinearIssue(
        id="AIM-123",
        title="Test feature implementation",
        description="Implement test feature for validation"
    )


@pytest.fixture
def sample_git_info() -> GitInfo:
    """Create sample git info for testing."""
    return GitInfo(
        repo_url="https://github.com/test/repo.git",
        base_branch="main",
        branch_name="feature/aim-123-test-feature",
        commits_ahead=0,
        commits_behind=0,
        modified_files=0,
        staged_files=0
    )


@pytest.fixture
def sample_workspace_metadata(
    temp_workspace_dir: Path,
    sample_linear_issue: LinearIssue,
    sample_git_info: GitInfo
) -> WorkspaceMetadata:
    """Create sample workspace metadata for testing."""
    return WorkspaceMetadata(
        name="aim-123-test-feature",
        path=temp_workspace_dir / "aim-123-test-feature",
        description="Test feature implementation",
        issue=sample_linear_issue,
        git=sample_git_info
    )


@pytest.fixture
def mock_git_repo():
    """Mock git repository for testing."""
    mock_repo = Mock()
    mock_repo.git.branch.return_value = "feature/aim-123-test-feature"
    mock_repo.git.status.return_value = "nothing to commit, working tree clean"
    mock_repo.heads = []
    mock_repo.remotes = []
    return mock_repo