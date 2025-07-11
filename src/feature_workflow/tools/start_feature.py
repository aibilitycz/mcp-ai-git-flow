"""MCP tool for starting a new feature workspace."""

from typing import Any, Dict, Optional

from ..server import FeatureWorkflowServer


async def start_feature_tool(
    issue_id: str,
    description: str,
    base_branch: Optional[str] = None
) -> Dict[str, Any]:
    """
    Start a new feature workspace using git worktrees.
    
    Args:
        issue_id: Linear issue ID (e.g., "AIM-123")
        description: Brief feature description
        base_branch: Base branch (optional, defaults to "main")
    
    Returns:
        Dictionary with workspace creation result
    """
    server = FeatureWorkflowServer()
    return await server.start_feature(
        issue_id=issue_id,
        description=description,
        base_branch=base_branch
    )