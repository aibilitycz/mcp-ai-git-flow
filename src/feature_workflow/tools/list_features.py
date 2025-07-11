"""MCP tool for listing feature workspaces."""

from typing import Any, Dict

from ..server import FeatureWorkflowServer


async def list_features_tool() -> Dict[str, Any]:
    """
    List all feature workspaces.
    
    Returns:
        Dictionary with list of workspaces and their status
    """
    server = FeatureWorkflowServer()
    return await server.list_features()