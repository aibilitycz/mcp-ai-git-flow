"""Unit tests for WorkspaceManager."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from feature_workflow.managers.workspace_manager import WorkspaceManager
from feature_workflow.models.workspace import WorkspaceStatus


class TestWorkspaceManager:
    """Test cases for WorkspaceManager."""
    
    @pytest.mark.asyncio
    async def test_create_workspace(self, test_config, temp_workspace_dir):
        """Test workspace creation."""
        manager = WorkspaceManager(test_config)
        
        # Create workspace
        workspace = await manager.create_workspace(
            issue_id="AIM-123",
            description="Test feature implementation",
            repo_url="https://github.com/test/repo.git",
            base_branch="main"
        )
        
        # Verify workspace was created
        assert workspace.name == "aim-123-test-feature-implementation"
        assert workspace.issue_id == "AIM-123"
        assert workspace.description == "Test feature implementation"
        assert workspace.git.repo_url == "https://github.com/test/repo.git"
        assert workspace.git.base_branch == "main"
        assert workspace.git.branch_name == "feature/aim-123-test-feature-implementation"
        assert workspace.path.exists()
        
        # Verify metadata file was created
        metadata_file = workspace.path / ".feature-metadata.json"
        assert metadata_file.exists()
        
        # Verify active workspace was set
        active_name = await manager.get_active_workspace_name()
        assert active_name == workspace.name
    
    @pytest.mark.asyncio
    async def test_create_workspace_duplicate(self, test_config, temp_workspace_dir):
        """Test creating duplicate workspace raises error."""
        manager = WorkspaceManager(test_config)
        
        # Create first workspace
        await manager.create_workspace(
            issue_id="AIM-123",
            description="Test feature",
            repo_url="https://github.com/test/repo.git"
        )
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            await manager.create_workspace(
                issue_id="AIM-123",
                description="Test feature",
                repo_url="https://github.com/test/repo.git"
            )
    
    @pytest.mark.asyncio
    async def test_list_workspaces(self, test_config, temp_workspace_dir):
        """Test listing workspaces."""
        manager = WorkspaceManager(test_config)
        
        # Initially empty
        workspace_list = await manager.list_workspaces()
        assert len(workspace_list.workspaces) == 0
        
        # Create some workspaces
        await manager.create_workspace(
            issue_id="AIM-123",
            description="First feature",
            repo_url="https://github.com/test/repo.git"
        )
        
        await manager.create_workspace(
            issue_id="AIM-124",
            description="Second feature",
            repo_url="https://github.com/test/repo.git"
        )
        
        # List workspaces
        workspace_list = await manager.list_workspaces()
        assert len(workspace_list.workspaces) == 2
        
        # Verify sorting (newest first)
        assert workspace_list.workspaces[0].issue_id == "AIM-124"
        assert workspace_list.workspaces[1].issue_id == "AIM-123"
        
        # Verify active workspace
        assert workspace_list.active_workspace == "aim-124-second-feature"
    
    @pytest.mark.asyncio
    async def test_switch_workspace(self, test_config, temp_workspace_dir):
        """Test switching between workspaces."""
        manager = WorkspaceManager(test_config)
        
        # Create workspaces
        workspace1 = await manager.create_workspace(
            issue_id="AIM-123",
            description="First feature",
            repo_url="https://github.com/test/repo.git"
        )
        
        workspace2 = await manager.create_workspace(
            issue_id="AIM-124",
            description="Second feature",
            repo_url="https://github.com/test/repo.git"
        )
        
        # Active should be the last created
        active_name = await manager.get_active_workspace_name()
        assert active_name == workspace2.name
        
        # Switch to first workspace
        await manager.set_active_workspace(workspace1.name)
        active_name = await manager.get_active_workspace_name()
        assert active_name == workspace1.name
        
        # Switch to non-existent workspace should raise error
        with pytest.raises(ValueError, match="not found"):
            await manager.set_active_workspace("non-existent")
    
    @pytest.mark.asyncio
    async def test_delete_workspace(self, test_config, temp_workspace_dir):
        """Test deleting workspace."""
        manager = WorkspaceManager(test_config)
        
        # Create workspace
        workspace = await manager.create_workspace(
            issue_id="AIM-123",
            description="Test feature",
            repo_url="https://github.com/test/repo.git"
        )
        
        # Verify it exists
        assert workspace.path.exists()
        active_name = await manager.get_active_workspace_name()
        assert active_name == workspace.name
        
        # Delete workspace
        success = await manager.delete_workspace(workspace.name)
        assert success
        
        # Verify it's gone
        assert not workspace.path.exists()
        active_name = await manager.get_active_workspace_name()
        assert active_name is None
        
        # Delete non-existent workspace
        success = await manager.delete_workspace("non-existent")
        assert not success
    
    @pytest.mark.asyncio
    async def test_workspace_name_generation(self, test_config, temp_workspace_dir):
        """Test workspace name generation."""
        manager = WorkspaceManager(test_config)
        
        # Test normal case
        name = manager._generate_workspace_name("AIM-123", "User Authentication System")
        assert name == "aim-123-user-authentication-system"
        
        # Test with special characters
        name = manager._generate_workspace_name("AIM-124", "Fix bug in API & Database!")
        assert name == "aim-124-fix-bug-in-api--database"
        
        # Test with long description
        long_desc = "This is a very long description that should be truncated"
        name = manager._generate_workspace_name("AIM-125", long_desc)
        assert len(name) <= 40  # Should be truncated
        assert name.startswith("aim-125-")
    
    @pytest.mark.asyncio
    async def test_max_workspaces_limit(self, test_config, temp_workspace_dir):
        """Test workspace limit enforcement."""
        manager = WorkspaceManager(test_config)
        
        # Create max number of workspaces
        for i in range(test_config.workspace.max_workspaces):
            await manager.create_workspace(
                issue_id=f"AIM-{i+1}",
                description=f"Feature {i+1}",
                repo_url="https://github.com/test/repo.git"
            )
        
        # Try to create one more
        with pytest.raises(ValueError, match="Maximum number of workspaces"):
            await manager.create_workspace(
                issue_id="AIM-999",
                description="Too many features",
                repo_url="https://github.com/test/repo.git"
            )