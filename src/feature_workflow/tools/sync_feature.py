"""MCP tool for syncing feature workspace with base branch."""

from typing import Any, Dict

from ..server import FeatureWorkflowServer


async def sync_feature_tool(
    workspace_name: str = None,
    strategy: str = "rebase"
) -> Dict[str, Any]:
    """
    Sync feature workspace with base branch.
    
    Args:
        workspace_name: Name of workspace to sync (optional, uses active if not provided)
        strategy: Sync strategy - "rebase" or "merge" (default: "rebase")
    
    Returns:
        Dictionary with sync result
    """
    server = FeatureWorkflowServer()
    
    try:
        # Get workspace name
        if not workspace_name:
            active_workspace = await server.workspace_manager.get_active_workspace()
            if not active_workspace:
                return {
                    "success": False,
                    "error": "No active workspace found and no workspace name provided"
                }
            workspace_name = active_workspace.name
        
        # Sync workspace
        commits_ahead, commits_behind, has_conflicts = await server.workspace_manager.sync_workspace(
            workspace_name, strategy
        )
        
        return {
            "success": True,
            "workspace_name": workspace_name,
            "strategy": strategy,
            "commits_ahead": commits_ahead,
            "commits_behind": commits_behind,
            "has_conflicts": has_conflicts,
            "message": f"Synced workspace {workspace_name} with base branch" + 
                      (" (conflicts detected)" if has_conflicts else "")
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }