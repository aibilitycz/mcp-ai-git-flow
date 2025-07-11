"""Command line interface for feature workflow MCP server."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import config
from .models.workspace import WorkspaceStatus

app = typer.Typer(
    name="feature-workflow-mcp",
    help="Feature Workflow MCP Server - Automated parallel feature development workflows",
    add_completion=False,
)
console = Console()


@app.command()
def version():
    """Show version information."""
    from . import __version__
    console.print(f"Feature Workflow MCP Server v{__version__}")


@app.command()
def config_show():
    """Show current configuration."""
    console.print("Current Configuration:")
    console.print(f"  Worktrees Directory: {config.workspace.worktrees_dir}")
    console.print(f"  Max Worktrees: {config.workspace.max_worktrees}")
    console.print(f"  Auto Cleanup Days: {config.workspace.auto_cleanup_days}")
    console.print(f"  Sync IDE Settings: {config.workspace.sync_ide_settings}")
    console.print(f"  IDE Config Dirs: {', '.join(config.workspace.ide_config_dirs)}")
    console.print(f"  Default Base Branch: {config.git.default_base_branch}")
    console.print(f"  Linear Issue Prefix: {config.linear.issue_prefix}")
    console.print(f"  Metadata Dir: {config.worktrees_metadata_dir}")
    console.print(f"  Debug Mode: {config.debug}")


@app.command()
def workspace_list():
    """List all feature workspaces."""
    import asyncio
    from .managers.workspace_manager import WorkspaceManager
    
    async def _list_workspaces():
        manager = WorkspaceManager(config)
        workspace_list = await manager.list_workspaces()
        
        if not workspace_list.workspaces:
            console.print("No workspaces found.")
            return
        
        table = Table(title="Feature Worktrees")
        table.add_column("Name", style="cyan")
        table.add_column("Issue", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Branch", style="blue")
        table.add_column("Active", style="yellow")
        table.add_column("Path", style="dim")
        
        for workspace in workspace_list.workspaces:
            is_active = "✓" if workspace.name == workspace_list.active_workspace else ""
            table.add_row(
                workspace.name,
                workspace.issue_id,
                workspace.status.value,
                workspace.branch_name,
                is_active,
                str(workspace.path)
            )
        
        console.print(table)
    
    asyncio.run(_list_workspaces())


@app.command()
def workspace_clean(
    days: int = typer.Option(7, "--days", "-d", help="Remove workspaces older than N days"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be cleaned without actually doing it"),
):
    """Clean up old workspaces."""
    workspace_dir = config.workspace_base_dir
    if not workspace_dir.exists():
        console.print("No workspaces found.")
        return
    
    # TODO: Implement cleanup logic
    if dry_run:
        console.print(f"Would clean workspaces older than {days} days")
    else:
        console.print(f"Cleaning workspaces older than {days} days...")


@app.command()
def server_start(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
):
    """Start the MCP server."""
    console.print(f"Starting Feature Workflow MCP Server on {host}:{port}")
    # TODO: Implement MCP server startup
    console.print("MCP server functionality not yet implemented")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()