# Feature Workflow MCP Server

An MCP (Model Context Protocol) server that automates parallel feature development workflows with Claude Code. This server enables isolated feature workspaces, automatic Linear issue integration via commit messages, and streamlined git operations.

## Features

- **🌳 Git Worktree Integration**: Modern parallel development using git worktrees
- **🏗️ Isolated Workspaces**: Separate development environments with shared git history
- **📋 Linear Integration**: Automatic issue tracking via commit message conventions
- **🤖 Git Automation**: Automated branch creation, commits, and PR management
- **⚡ Parallel Development**: Work on multiple features simultaneously without conflicts
- **🔧 IDE Settings Sync**: Automatic copying of .vscode, .cursor, .idea configs
- **🧠 Claude Code Integration**: Seamless workflow with Claude Code AI assistant

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/aibility/feature-workflow-mcp.git
cd feature-workflow-mcp

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Show version
feature-workflow-mcp version

# Show configuration
feature-workflow-mcp config-show

# List workspaces
feature-workflow-mcp workspace-list

# Clean old workspaces
feature-workflow-mcp workspace-clean --days 7
```

### MCP Server

```bash
# Start the MCP server
feature-workflow-mcp server-start
```

## Linear Integration

This server integrates with Linear through simple commit message conventions:

- **`Part of AIM-123`** - Links commit to Linear issue AIM-123
- **`Fixes AIM-123`** - Links commit and closes Linear issue AIM-123

## Workspace Structure (Git Worktrees)

```
your-project/                          # Main repository
├── .git/                              # Shared git repository
├── .feature-workflow/                 # MCP metadata
│   ├── active-workspace               # Current active workspace
│   ├── aim-102.json                   # Feature metadata
│   └── aim-103.json                   # Another feature metadata
├── worktrees/                         # Git worktrees directory
│   ├── aim-102-user-permissions/      # Feature worktree
│   │   ├── .git                       # Worktree git link
│   │   ├── .vscode/                   # Synced IDE settings
│   │   ├── .cursor/                   # Synced AI context
│   │   └── [all project files]       # Full project access
│   └── aim-103-ai-integration/        # Another feature worktree
└── [main project files]               # Main development workspace
```

## Configuration

Configuration is managed through environment variables with the `FEATURE_WORKFLOW_` prefix:

```bash
# Worktree settings
FEATURE_WORKFLOW_WORKSPACE__WORKTREES_DIR="worktrees"
FEATURE_WORKFLOW_WORKSPACE__MAX_WORKTREES=10
FEATURE_WORKFLOW_WORKSPACE__AUTO_CLEANUP_DAYS=7
FEATURE_WORKFLOW_WORKSPACE__SYNC_IDE_SETTINGS=true

# Git settings
FEATURE_WORKFLOW_GIT__DEFAULT_BASE_BRANCH="main"
FEATURE_WORKFLOW_GIT__USER_NAME="Claude Code"
FEATURE_WORKFLOW_GIT__USER_EMAIL="claude@anthropic.com"

# Linear settings
FEATURE_WORKFLOW_LINEAR__ISSUE_PREFIX="AIM"

# GitHub/GitLab (optional)
FEATURE_WORKFLOW_GITHUB__TOKEN="your-github-token"
FEATURE_WORKFLOW_GITHUB__REPO="owner/repo"
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov=feature_workflow

# Format code
black src tests
ruff check src tests

# Type checking
mypy src
```

### Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run integration tests only
pytest tests/integration

# Run with coverage
pytest --cov=feature_workflow --cov-report=html
```

## Architecture

The server is built with modern Python technologies:

- **Python 3.10+** with async/await support
- **Pydantic 2.11.7** for data validation and settings
- **GitPython** for git operations
- **httpx** for HTTP client operations
- **typer** for CLI interface
- **pytest** for testing

## Contributing

1. Follow the development best practices outlined in `CLAUDE.md`
2. Use TDD (Test-Driven Development) approach
3. Ensure all tests pass and maintain code coverage
4. Follow the YAGNI principle - implement only what's needed
5. Use conventional commits for Linear integration

## License

MIT License - see LICENSE file for details.