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

#### Method 1: Direct Installation via uv (Recommended)
```bash
# Install and run directly (no cloning needed)
uvx --from git+https://github.com/aibility/feature-workflow-mcp feature-workflow-mcp --help

# For Claude Code
claude mcp add feature-workflow -- uvx --from git+https://github.com/aibility/feature-workflow-mcp feature-workflow-mcp --args server-start

# For Cursor (.cursor/mcp.json)
{
  "mcpServers": {
    "feature-workflow": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/aibility/feature-workflow-mcp", "feature-workflow-mcp", "server-start"]
    }
  }
}
```

#### Method 2: PyPI Installation (Coming Soon)
```bash
# Once published to PyPI
pip install feature-workflow-mcp

# Or with uv
uv add feature-workflow-mcp
uvx feature-workflow-mcp --help
```

#### Method 3: Development Installation
```bash
# Clone the repository for development
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

## Usage with Claude Code and Cursor

### 🧠 Claude Code Integration

#### Method 1: Claude CLI with uvx (Recommended)
Use the Claude CLI to add the MCP server directly from GitHub:

```bash
# Navigate to your project directory
cd /path/to/your-project

# Add the MCP server using uvx (no installation needed)
claude mcp add feature-workflow -- uvx --from git+https://github.com/aibility/feature-workflow-mcp feature-workflow-mcp --args server-start

# With environment variables
claude mcp add feature-workflow -- uvx --from git+https://github.com/aibility/feature-workflow-mcp feature-workflow-mcp \
  --args server-start \
  --env FEATURE_WORKFLOW_WORKSPACE__SYNC_IDE_SETTINGS=true \
  --env FEATURE_WORKFLOW_LINEAR__ISSUE_PREFIX=AIM

# Verify the server was added
claude mcp list
```

#### Method 2: Manual Configuration with uvx
Add to your Claude Code configuration (`.claude/mcp.json`):

```json
{
  "servers": {
    "feature-workflow": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/aibility/feature-workflow-mcp", "feature-workflow-mcp", "server-start"],
      "env": {
        "FEATURE_WORKFLOW_WORKSPACE__SYNC_IDE_SETTINGS": "true",
        "FEATURE_WORKFLOW_LINEAR__ISSUE_PREFIX": "AIM"
      }
    }
  }
}
```

#### Method 3: Local Installation (Development)
If you've installed locally:

```json
{
  "servers": {
    "feature-workflow": {
      "command": "feature-workflow-mcp",
      "args": ["server-start"],
      "env": {
        "FEATURE_WORKFLOW_WORKSPACE__SYNC_IDE_SETTINGS": "true",
        "FEATURE_WORKFLOW_LINEAR__ISSUE_PREFIX": "AIM"
      }
    }
  }
}
```

#### Step 2: Start Feature Development
In your project directory with Claude Code:

```bash
# User instruction to Claude
User: "Let's work on implementing user authentication for AIM-123"

# Claude automatically uses MCP tools
Claude: *uses start_feature MCP tool*
        "I've created a worktree for AIM-123 at: ./worktrees/aim-123-user-authentication
         
         Your IDE settings have been synced to the worktree.
         Please open this directory in a new window to continue development."
```

#### Step 3: Switch Context
```bash
# Open new terminal/Claude Code window in the worktree
cd ./worktrees/aim-123-user-authentication

# Continue development with Claude in the isolated workspace
User: "Implement the authentication middleware"
Claude: # Works normally with all project context and tooling
```

#### Step 4: Commit and Manage
```bash
User: "Commit our progress"
Claude: *uses commit_feature MCP tool*
        "Committed changes with Linear issue reference: 'Part of AIM-123'"

User: "Let's work on a different feature now"
Claude: *uses switch_feature or start_feature MCP tool*
        "Switched to feature workspace AIM-124..."
```

### 🖱️ Cursor IDE Integration

#### Step 1: Setup MCP in Cursor

Create or update the MCP configuration file at `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "feature-workflow": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/aibility/feature-workflow-mcp", "feature-workflow-mcp", "server-start"],
      "env": {
        "FEATURE_WORKFLOW_WORKSPACE__SYNC_IDE_SETTINGS": "true",
        "FEATURE_WORKFLOW_LINEAR__ISSUE_PREFIX": "AIM",
        "FEATURE_WORKFLOW_WORKSPACE__WORKTREES_DIR": "worktrees",
        "FEATURE_WORKFLOW_GIT__DEFAULT_BASE_BRANCH": "main"
      }
    }
  }
}
```

**Alternative (if installed locally):**
```json
{
  "mcpServers": {
    "feature-workflow": {
      "command": "feature-workflow-mcp",
      "args": ["server-start"],
      "env": {
        "FEATURE_WORKFLOW_WORKSPACE__SYNC_IDE_SETTINGS": "true",
        "FEATURE_WORKFLOW_LINEAR__ISSUE_PREFIX": "AIM",
        "FEATURE_WORKFLOW_WORKSPACE__WORKTREES_DIR": "worktrees",
        "FEATURE_WORKFLOW_GIT__DEFAULT_BASE_BRANCH": "main"
      }
    }
  }
}
```

Alternative locations for the configuration file:
- **Project-specific**: `.cursor/mcp.json` (recommended for project-specific workflows)
- **Global**: `~/.cursor/mcp.json` (for use across all projects)

#### Step 2: Verify MCP Server
After creating the configuration:

1. **Restart Cursor** to load the new MCP server
2. **Open the project** where you added the configuration
3. **Check Cursor's output panel** for MCP server logs
4. **Test the integration** by asking Cursor to list features or start a new feature

#### Step 3: Natural Language Workflow
```bash
# In your main project with Cursor AI
User: "Create a new feature workspace for implementing payment processing (AIM-124)"

# Cursor uses MCP server
Cursor AI: "I've created a worktree at ./worktrees/aim-124-payment-processing
           Opening the workspace now..."

# Cursor automatically opens new window with the worktree
# All extensions, settings, and AI context work normally
```

#### Step 4: Parallel Development
```bash
# Multiple Cursor windows can work on different features simultaneously
Window 1: ./worktrees/aim-123-auth (Authentication feature)
Window 2: ./worktrees/aim-124-payments (Payment feature)  
Window 3: ./ (Main project for reviews/coordination)

# Each workspace has:
✅ Full project files and history
✅ Synced .cursor/ AI context
✅ Synced .vscode/ settings
✅ Independent git branches
✅ No merge conflicts between features
```

### 🔄 Complete Workflow Example

```bash
# 1. Start new feature (in main project)
User: "Let's implement user permissions for AIM-125"
AI: *creates worktree with synced settings*

# 2. Open worktree in new IDE window
# File: ./worktrees/aim-125-user-permissions/
# - All IDE features work normally
# - Full project context available
# - Git branch: feature/aim-125-user-permissions

# 3. Develop feature with AI assistance
User: "Add role-based permission middleware"
AI: *implements feature with full context*

# 4. Commit progress
User: "Commit this implementation"
AI: *uses commit_feature MCP tool*
    "Committed: 'Add role-based permission middleware - Part of AIM-125'"

# 5. Sync with latest changes
User: "Sync with main branch"
AI: *uses sync_feature MCP tool*
    "Synced worktree with main - no conflicts detected"

# 6. Complete feature
User: "This feature is done, create PR"
AI: *uses finish_feature MCP tool*
    "Created PR #42 and cleaned up worktree"

# 7. Switch to next feature
User: "Now let's work on AIM-126 dashboard improvements"
AI: *starts new worktree for next feature*
```

### 🎯 Pro Tips for AI-Assisted Development

#### Best Practices:
1. **Start each feature conversation** by mentioning the Linear issue ID
2. **Let the AI manage worktrees** - it knows when to create, switch, and sync
3. **Use descriptive feature names** for better workspace organization
4. **Open worktrees in separate IDE windows** for parallel development
5. **Commit frequently** with AI assistance for proper Linear integration

#### Command Examples:
```bash
# Natural language commands that trigger MCP tools:
"Start working on AIM-123 user authentication"      → start_feature
"Show me all active features"                       → list_features  
"Switch to the payment processing feature"          → switch_feature
"Commit our authentication changes"                 → commit_feature
"Sync this feature with the latest main branch"     → sync_feature
"We're done with this feature, create a PR"         → finish_feature
"Clean up old completed features"                   → cleanup_features
```

#### IDE Settings Synced Automatically:
- **VS Code**: `.vscode/settings.json`, extensions, workspace config
- **Cursor**: `.cursor/` AI context, custom prompts, preferences  
- **IntelliJ/PyCharm**: `.idea/` project settings, code styles
- **Custom configs**: Add to `FEATURE_WORKFLOW_WORKSPACE__IDE_CONFIG_DIRS`

### 🔧 Troubleshooting MCP Setup

#### Common Issues:

**1. "MCP server not found" error:**
```bash
# Ensure the package is installed
pip install -e .

# Verify the command is available
which feature-workflow-mcp

# Check if virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**2. "Permission denied" errors:**
```bash
# Make sure the script is executable
chmod +x $(which feature-workflow-mcp)
```

**3. Cursor not loading MCP configuration:**
- Restart Cursor completely after adding `.cursor/mcp.json`
- Check the configuration file syntax with a JSON validator
- Verify the file is in the correct location (project root or `~/.cursor/`)
- Check Cursor's output panel for error messages

**4. Claude CLI issues:**
```bash
# Update Claude CLI to latest version
claude --version

# Re-add the MCP server if needed
claude mcp remove feature-workflow
claude mcp add feature-workflow feature-workflow-mcp --args server-start
```

**5. Environment variables not loading:**
- Create a `.env` file based on `.env.example`
- Ensure environment variables are properly set
- Restart the IDE after changing environment configuration

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