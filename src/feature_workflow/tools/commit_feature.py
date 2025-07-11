"""MCP tool for committing feature changes."""

from typing import Any, Dict

from ..server import FeatureWorkflowServer


async def commit_feature_tool(
    message: str,
    close_issue: bool = False
) -> Dict[str, Any]:
    """
    Commit changes in the active workspace with Linear issue reference.
    
    Args:
        message: Commit message
        close_issue: Whether this commit closes the issue (default: False)
    
    Returns:
        Dictionary with commit result
    """
    server = FeatureWorkflowServer()
    return await server.commit_feature(
        message=message,
        close_issue=close_issue
    )