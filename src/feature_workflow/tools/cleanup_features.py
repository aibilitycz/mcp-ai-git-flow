"""MCP tool for cleaning up old workspaces."""

from typing import Any, Dict

from ..server import FeatureWorkflowServer


async def cleanup_features_tool(
    older_than_days: int = 7,
    completed_only: bool = True
) -> Dict[str, Any]:
    """
    Clean up old feature workspaces.
    
    Args:
        older_than_days: Remove workspaces older than N days (default: 7)
        completed_only: Only clean completed features (default: True)
    
    Returns:
        Dictionary with cleanup result
    """
    server = FeatureWorkflowServer()
    return await server.cleanup_features(
        older_than_days=older_than_days,
        completed_only=completed_only
    )