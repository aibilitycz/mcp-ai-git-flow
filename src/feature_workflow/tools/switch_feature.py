"""MCP tool for switching feature workspaces."""

from typing import Any, Dict

from ..server import FeatureWorkflowServer


async def switch_feature_tool(workspace_name: str) -> Dict[str, Any]:
    """
    Switch to a different feature workspace.
    
    Args:
        workspace_name: Name of the workspace to switch to
    
    Returns:
        Dictionary with switch result
    """
    server = FeatureWorkflowServer()
    return await server.switch_feature(workspace_name)