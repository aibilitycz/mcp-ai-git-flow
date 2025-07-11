# Feature Workflow MCP Server

## Overview

This document outlines the design and implementation plan for a **Feature Workflow MCP Server** that automates the complete development workflow for parallel feature development with Claude Code. The server enables isolated feature workspaces, automatic Linear issue integration, and streamlined git operations.

## Problem Statement

### Current Challenges
- **Git workspace conflicts**: Multiple Claude Code instances cannot work simultaneously in the same directory
- **Manual coordination**: Setting up feature branches, workspaces, and Linear issue tracking requires manual steps
- **Context switching overhead**: Developers must manually manage multiple feature branches and workspaces
- **Inconsistent workflows**: No standardized process for feature development, commits, and PR creation

### Goals
1. **Parallel Development**: Enable multiple Claude Code instances to work on different features simultaneously
2. **Automated Workflows**: Reduce manual overhead in feature branch management and issue tracking
3. **Linear Integration**: Automatic connection between code changes and Linear issues
4. **Clean Workspaces**: Automatic cleanup and workspace management
5. **Standardized Process**: Consistent development workflow across all features

## Architecture Overview

### MCP Server: `feature-workflow`

The MCP server provides tools for managing isolated feature development workspaces with full git and Linear integration.

```
┌─────────────────────────────────────────────────────────────┐
│                 Feature Workflow MCP Server                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Workspace     │  │   Git Manager   │  │   Linear    │ │
│  │   Manager       │  │                 │  │ Integration │ │
│  │                 │  │ • Branch ops    │  │             │ │
│  │ • Create        │  │ • Commit        │  │ • Issue     │ │
│  │ • Switch        │  │ • Push          │  │   tracking  │ │
│  │ • Cleanup       │  │ • PR creation   │  │ • Status    │ │
│  │ • List          │  │                 │  │   updates   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    File System Layout                      │
│                                                             │
│  /tmp/claude-features/                                      │
│  ├── aim-102-user-permissions/          # Feature workspace │
│  │   ├── .git/                          # Isolated git     │
│  │   ├── backend/                       # Full repo clone  │
│  │   └── .feature-metadata.json         # Workspace info   │
│  ├── aim-103-ai-integration/            # Another feature  │
│  └── .active-workspace                  # Current context  │
└─────────────────────────────────────────────────────────────┘
```

## MCP Tools Specification

### Core Tools

#### 1. `start_feature`
**Purpose**: Create isolated workspace and branch for new feature development

**Parameters**:
- `issue_id` (required): Linear issue ID (e.g., "AIM-102")
- `description` (required): Brief feature description
- `repo_url` (optional): Repository URL (defaults to current repo)
- `base_branch` (optional): Base branch (defaults to "main")

**Behavior**:
1. Create workspace directory: `/tmp/claude-features/{issue_id}-{slug(description)}/`
2. Clone repository into workspace
3. Create feature branch: `feature/{issue_id}-{slug(description)}`
4. Set workspace as active context
5. Create `.feature-metadata.json` with issue tracking info
6. Return workspace path and branch info

**Output**:
```json
{
  "success": true,
  "workspace_path": "/tmp/claude-features/aim-102-user-permissions",
  "branch_name": "feature/aim-102-user-permissions",
  "issue_id": "AIM-102",
  "linear_url": "https://linear.app/aibility/issue/AIM-102"
}
```

#### 2. `list_features`
**Purpose**: Show all active feature workspaces

**Parameters**: None

**Behavior**:
1. Scan `/tmp/claude-features/` for workspaces
2. Read metadata from each workspace
3. Show current status (active, branch, commits ahead)

**Output**:
```json
{
  "workspaces": [
    {
      "name": "aim-102-user-permissions",
      "path": "/tmp/claude-features/aim-102-user-permissions",
      "branch": "feature/aim-102-user-permissions",
      "issue_id": "AIM-102",
      "description": "User scenario permissions",
      "commits_ahead": 3,
      "last_commit": "2025-01-11T10:30:00Z",
      "is_active": true
    }
  ]
}
```

#### 3. `switch_feature`
**Purpose**: Switch active workspace context

**Parameters**:
- `workspace_name` (required): Name of workspace to switch to

**Behavior**:
1. Validate workspace exists
2. Update `.active-workspace` file
3. Change Claude Code working directory context

#### 4. `commit_feature`
**Purpose**: Commit changes with Linear issue reference

**Parameters**:
- `message` (required): Commit message
- `close_issue` (optional): Whether this closes the issue (default: false)

**Behavior**:
1. Stage all changes in active workspace
2. Create commit with enhanced message:
   ```
   {message}
   
   {close_issue ? "Closes" : "Part of"} {issue_id}
   
   🤖 Generated with [Claude Code](https://claude.ai/code)
   
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
3. Update Linear issue with commit reference

#### 5. `finish_feature`
**Purpose**: Complete feature development workflow

**Parameters**:
- `pr_title` (optional): Pull request title
- `pr_description` (optional): Pull request description
- `cleanup` (optional): Delete workspace after PR (default: true)

**Behavior**:
1. Final commit with "Closes {issue_id}"
2. Push branch to origin
3. Create GitHub/GitLab pull request
4. Link PR to Linear issue
5. Optionally cleanup workspace
6. Switch back to main directory

#### 6. `cleanup_features`
**Purpose**: Clean up old or completed workspaces

**Parameters**:
- `older_than_days` (optional): Remove workspaces older than N days (default: 7)
- `completed_only` (optional): Only clean completed features (default: true)

### Utility Tools

#### 7. `sync_feature`
**Purpose**: Sync feature branch with latest base branch

**Parameters**:
- `strategy` (optional): "rebase" or "merge" (default: "rebase")

#### 8. `feature_status`
**Purpose**: Get detailed status of current feature

**Parameters**: None

**Output**:
```json
{
  "workspace": "aim-102-user-permissions",
  "branch": "feature/aim-102-user-permissions",
  "issue": {
    "id": "AIM-102",
    "title": "Implement user scenario permissions",
    "status": "In Progress",
    "assignee": "ondrej@aibility.cz"
  },
  "git": {
    "commits_ahead": 3,
    "commits_behind": 0,
    "modified_files": 5,
    "staged_files": 0
  }
}
```

## Workflow Integration

### Natural Language Commands

The MCP server integrates seamlessly with Claude Code's natural language interface:

```
User: "Let's work on implementing user permissions for AIM-102"
Claude: *uses start_feature MCP tool*
        "I've created a workspace for AIM-102 user permissions. 
         Working in: /tmp/claude-features/aim-102-user-permissions
         Let me start implementing the feature..."

User: "Commit our progress"
Claude: *uses commit_feature MCP tool*
        "Committed changes with message 'Add user permission schema - Part of AIM-102'"

User: "We're done with this feature"
Claude: *uses finish_feature MCP tool*
        "Created PR #123 for AIM-102 and cleaned up workspace.
         PR: https://github.com/aibility/aimee/pull/123"
```

### Slash Commands

For power users, direct slash commands provide quick access:

```bash
/start-feature AIM-102 "user scenario permissions"
/switch-feature aim-103-ai-integration
/commit "Add new authentication flow"
/finish-feature --no-cleanup
/list-features
/cleanup-features --older-than-days 3
```

## Implementation Plan

### Phase 1: Core MCP Server (Week 1-2)

#### 1.1 Project Setup
- [ ] Create `feature-workflow-mcp` Python project
- [ ] Set up MCP server boilerplate
- [ ] Configure development environment
- [ ] Create basic project structure

#### 1.2 Workspace Management
- [ ] Implement `WorkspaceManager` class
- [ ] Add workspace creation and deletion
- [ ] Implement workspace metadata system
- [ ] Add workspace switching logic

#### 1.3 Git Integration
- [ ] Implement `GitManager` class
- [ ] Add repository cloning
- [ ] Implement branch creation and switching
- [ ] Add commit operations with enhanced messages

#### 1.4 Basic MCP Tools
- [ ] Implement `start_feature` tool
- [ ] Implement `list_features` tool
- [ ] Implement `switch_feature` tool
- [ ] Implement `commit_feature` tool

### Phase 2: Linear Integration (Week 3)

#### 2.1 Linear API Client
- [ ] Create Linear API client
- [ ] Implement issue fetching
- [ ] Add issue status updates
- [ ] Add commit linking to issues

#### 2.2 Enhanced Tools
- [ ] Update `start_feature` with Linear integration
- [ ] Update `commit_feature` with issue tracking
- [ ] Implement `feature_status` tool
- [ ] Add issue validation and error handling

### Phase 3: PR Automation (Week 4)

#### 3.1 GitHub/GitLab Integration
- [ ] Create GitHub API client
- [ ] Implement PR creation
- [ ] Add PR templating
- [ ] Link PRs to Linear issues

#### 3.2 Completion Workflow
- [ ] Implement `finish_feature` tool
- [ ] Add automated PR creation
- [ ] Implement workspace cleanup
- [ ] Add completion notifications

### Phase 4: Advanced Features (Week 5-6)

#### 4.1 Synchronization
- [ ] Implement `sync_feature` tool
- [ ] Add conflict resolution guidance
- [ ] Add base branch update checking

#### 4.2 Cleanup and Maintenance
- [ ] Implement `cleanup_features` tool
- [ ] Add automatic workspace management
- [ ] Add disk space monitoring

#### 4.3 Claude Code Integration
- [ ] Add slash command support
- [ ] Implement natural language processing
- [ ] Add context-aware suggestions

### Phase 5: Production Deployment (Week 7)

#### 5.1 Configuration
- [ ] Add configuration file support
- [ ] Implement environment-specific settings
- [ ] Add security considerations

#### 5.2 Testing and Documentation
- [ ] Comprehensive testing suite
- [ ] User documentation
- [ ] Integration testing with Claude Code

#### 5.3 Deployment
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Production deployment guide

## Technical Specifications

### File Structure

```
feature-workflow-mcp/
├── src/
│   ├── feature_workflow/
│   │   ├── __init__.py
│   │   ├── server.py              # Main MCP server
│   │   ├── workspace_manager.py   # Workspace operations
│   │   ├── git_manager.py         # Git operations
│   │   ├── linear_client.py       # Linear API integration
│   │   ├── github_client.py       # GitHub API integration
│   │   ├── models.py              # Data models
│   │   └── config.py              # Configuration
│   └── tools/
│       ├── __init__.py
│       ├── start_feature.py
│       ├── list_features.py
│       ├── switch_feature.py
│       ├── commit_feature.py
│       ├── finish_feature.py
│       └── cleanup_features.py
├── tests/
├── docs/
├── docker/
├── requirements.txt
├── setup.py
└── README.md
```

### Configuration

```python
# config.py
@dataclass
class FeatureWorkflowConfig:
    # Workspace settings
    workspace_base_dir: str = "/tmp/claude-features"
    default_repo_url: str = ""
    default_base_branch: str = "main"
    
    # Linear integration
    linear_api_key: str = ""
    linear_team_id: str = ""
    
    # GitHub integration
    github_token: str = ""
    github_repo: str = ""
    
    # Cleanup settings
    auto_cleanup_days: int = 7
    max_workspaces: int = 10
    
    # Git settings
    git_user_name: str = "Claude Code"
    git_user_email: str = "claude@anthropic.com"
```

### Workspace Metadata

```json
{
  "version": "1.0",
  "created_at": "2025-01-11T10:00:00Z",
  "issue_id": "AIM-102",
  "description": "User scenario permissions",
  "branch_name": "feature/aim-102-user-permissions",
  "base_branch": "main",
  "repo_url": "https://github.com/aibility/aimee-backend.git",
  "linear_issue": {
    "id": "AIM-102",
    "title": "Implement user scenario permissions",
    "url": "https://linear.app/aibility/issue/AIM-102"
  },
  "commits": [],
  "status": "active"
}
```

## Security Considerations

1. **API Key Management**: Secure storage and rotation of Linear/GitHub tokens
2. **Workspace Isolation**: Proper file permissions and sandbox isolation
3. **Git Credentials**: Safe handling of git authentication
4. **Cleanup**: Automatic cleanup of sensitive data in temporary workspaces

## Benefits

### For Developers
- **Parallel Development**: Work on multiple features simultaneously
- **Reduced Context Switching**: Automatic workspace management
- **Consistent Workflows**: Standardized process across all features
- **Automatic Tracking**: Linear issue integration without manual effort

### For Teams
- **Better Visibility**: Clear connection between code and Linear issues
- **Faster Reviews**: Consistent PR format and automatic linking
- **Reduced Conflicts**: Isolated development environments
- **Clean History**: Standardized commit messages and branch naming

### For Claude Code
- **Enhanced Capabilities**: New workflow automation tools
- **Better Context**: Understanding of current feature being worked on
- **Improved UX**: Seamless integration with development workflow
- **Scalability**: Support for complex, multi-feature development

## Success Metrics

1. **Development Velocity**: Reduce feature setup time from 5 minutes to 30 seconds
2. **Parallel Development**: Enable 3+ concurrent features per developer
3. **Issue Tracking**: 100% automatic Linear issue linking
4. **Workspace Management**: Zero manual cleanup required
5. **Developer Satisfaction**: Reduce context switching overhead by 70%

## Future Enhancements

### Advanced Features
- **Dependency Management**: Automatic detection and handling of feature dependencies
- **Conflict Resolution**: AI-powered merge conflict resolution
- **Performance Monitoring**: Workspace resource usage tracking
- **Team Collaboration**: Shared workspace features for pair programming

### Integration Opportunities
- **Jira Integration**: Support for Jira project management
- **Slack Integration**: Notifications and status updates
- **CI/CD Integration**: Automatic pipeline triggering
- **Code Review**: Integration with review tools and quality gates

This MCP server will transform the development workflow by providing automated, intelligent management of feature development from conception to completion, enabling true parallel development with Claude Code while maintaining clean, trackable, and efficient workflows.