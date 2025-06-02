# GitLab MCP Server# gitlab-mcp-server

> **⚠️ Development Stage Notice**  
> This project is currently in **development stage**. Features and APIs may change without notice. Use with caution in production environments.


GitLab MCP server based on [python-gitlab](https://github.com/python-gitlab/python-gitlab).



## Install

```json
{
  "mcpServers": {
    "GitLab": {
      "command": "uvx",
      "args": [
        "gitlab-mcp-server"
      ],
      "env": {
        "GITLAB_TOKEN": "<your GitLab personal access token>",
        "GITLAB_URL": "https://gitlab.com"
      }
    }
  }
}
```

For self-hosted GitLab instances, set `GITLAB_URL` to your GitLab instance URL (e.g., `https://gitlab.example.com`). If not set, it defaults to `https://gitlab.com`.

## Authentication

1. Create a GitLab Personal Access Token:
   - Go to GitLab → User Settings → Access Tokens
   - Create a token with `read_api` scope (minimum required)

2. Set the `GITLAB_TOKEN` environment variable to your token value

## Tools

- **list_projects** - List GitLab projects accessible to the authenticated user (supports filtering by owned/starred and pagination)
- **list_groups** - List GitLab groups accessible to the authenticated user
- **list_group_projects** - List all projects within a specific GitLab group
- **get_user_info** - Get information about the authenticated user
- **search_repositories** - Search for GitLab repositories by name, description, or keywords
- **get_repository_details** - Get detailed information about a specific repository

## Development

```bash
# Clone the repository
git clone <repo-url>
cd gitlab-mcp-server

# Install dependencies
uv sync

# Run in development mode
uv run python -m gitlab_mcp_server
```

### Testing Configuration

For development and testing purposes, you can use a local wheel file installation:

**MCP Configuration for Testing:**
```json
{
  "mcpServers": {
    "GitLab": {
      "command": "uvx",
      "args": [
        "--from", "/path/to/your/gitlab-mcp-server/dist/gitlab_mcp_server-0.1.0-py3-none-any.whl",
        "gitlab-mcp-server"
      ],
      "env": {
        "GITLAB_TOKEN": "your-gitlab-token-here",
        "GITLAB_URL": "https://gitlab.com"
      }
    }
  }
}
```

**Build and Test Steps:**
```bash
# Build the wheel file
uv build

# Test with MCP client (like Claude Desktop)
# Update your MCP configuration with the local wheel path
# The wheel file will be in ./dist/ directory

# For quick testing, verify the server starts:
uv run python -m gitlab_mcp_server
```
