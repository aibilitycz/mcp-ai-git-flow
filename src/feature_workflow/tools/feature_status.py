"""MCP tool for getting feature status."""

from typing import Any, Dict

from ..server import FeatureWorkflowServer


async def feature_status_tool() -> Dict[str, Any]:
    """
    Get detailed status of the current active feature.
    
    Returns:
        Dictionary with current feature status
    """
    server = FeatureWorkflowServer()
    return await server.feature_status()