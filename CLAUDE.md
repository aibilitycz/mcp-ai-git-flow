# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains the design specification for a **Feature Workflow MCP Server** - an MCP (Model Context Protocol) server that automates parallel feature development workflows with Claude Code. The project aims to solve git workspace conflicts, automate Linear issue integration, and streamline development workflows.

## Repository Structure

This is currently a design/specification repository containing a single comprehensive document:

- `feature-workflow-mcp-server.md` - Complete design specification and implementation plan for the MCP server

## Architecture Overview

The planned MCP server will provide:

1. **Workspace Management**: Isolated feature development environments in `/tmp/claude-features/`
2. **Git Integration**: Automated branch creation, commits, and PR management
3. **Linear Integration**: Automatic issue tracking and status updates
4. **Workflow Automation**: End-to-end feature development lifecycle

### Key Components (Planned)

- **Workspace Manager**: Creates and manages isolated development environments
- **Git Manager**: Handles all git operations with enhanced commit messages
- **Linear Integration**: Connects code changes to Linear issues automatically, simple, through "Part of AIM-XX" where XX is the issue number or "Fixes AIM-XX" when the feature is done and can be closed (mainly for bugs really)
- **PR Automation**: Creates pull requests with proper linking and cleanup

## MCP Tools (Planned)

The server will provide these MCP tools:

1. `start_feature` - Create isolated workspace for feature development
2. `list_features` - Show all active feature workspaces
3. `switch_feature` - Switch between feature workspaces
4. `commit_feature` - Commit with Linear issue references
5. `finish_feature` - Complete feature with PR creation and cleanup
6. `cleanup_features` - Remove old workspaces
7. `sync_feature` - Sync feature branch with base branch
8. `feature_status` - Get detailed status of current feature

## Implementation Plan

The project is structured in 5 phases:

1. **Phase 1**: Core MCP server and workspace management
2. **Phase 2**: Linear API integration
3. **Phase 3**: GitHub/GitLab PR automation
4. **Phase 4**: Advanced features and synchronization
5. **Phase 5**: Production deployment

## Development Context

This is a specification repository for planning the MCP server implementation. The actual implementation will be a separate Python project with the structure defined in the specification document.

## Key Design Decisions

- Uses temporary directories (`/tmp/claude-features/`) for workspace isolation
- Implements automatic Linear issue tracking through commit messages
- Provides both natural language and slash command interfaces
- Includes automatic cleanup and maintenance features
- Designed for parallel development workflows with Claude Code

## Development Best Practices

This project adheres to industry-leading software engineering principles from Martin Fowler, Andrew Ng, and MCP development standards:

### YAGNI (You Aren't Gonna Need It) - Martin Fowler
- **Core Principle**: Implement features only when actually needed, not when anticipated
- **Application**: Build MCP tools incrementally, starting with essential workspace management
- **Benefits**: Reduces complexity, prevents over-engineering, maintains lean codebase
- **Implementation**: Focus on current phase requirements, avoid presumptive features

### Data-Centric Engineering - Andrew Ng
- **Deployment-First Design**: Design from deployment backwards to data requirements
- **Iterative Development**: Use short development cycles (1-day sprints) for rapid experimentation
- **Production-Ready Systems**: Emphasize monitoring, concept drift detection, and maintenance
- **ML Engineering**: Apply systematic approaches to model lifecycle management

### MCP Development Standards (2024-2025)
- **Security First**: Implement OAuth Resource Server patterns with token protection
- **Architecture**: Follow client-server model with JSON-RPC protocol
- **Tool Safety**: Treat tools as arbitrary code execution with explicit user consent
- **Resource Management**: Use MCP primitives (Tools, Resources, Prompts) appropriately
- **Enterprise Scale**: Design for distributed deployment across infrastructure

### Implementation Guidelines
1. **Start Simple**: Begin with core functionality, iterate based on actual usage
2. **Security by Design**: Implement proper authorization and access controls from start
3. **Monitoring**: Include comprehensive logging and health checks
4. **Documentation**: Maintain clear API documentation and usage examples
5. **Testing**: Implement comprehensive testing for all MCP tools and workflows, TDD prefered
6. **Cleanup**: Ensure proper resource cleanup and workspace management