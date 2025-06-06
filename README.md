# mcp-gitlab-server

> **⚠️ Development Stage Notice**  
> This project is currently in **development stage**. Features and APIs may change without notice. Use with caution in production environments.


GitLab MCP server based on [python-gitlab](https://github.com/python-gitlab/python-gitlab).



## Install

### Using Personal Access Token (Most Common)
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

### Using OAuth2 Token
```json
{
  "mcpServers": {
    "GitLab": {
      "command": "uvx",
      "args": [
        "gitlab-mcp-server"
      ],
      "env": {
        "GITLAB_OAUTH_TOKEN": "<your GitLab OAuth2 token>",
        "GITLAB_URL": "https://gitlab.com"
      }
    }
  }
}
```

For self-hosted GitLab instances, set `GITLAB_URL` to your GitLab instance URL (e.g., `https://gitlab.example.com`). If not set, it defaults to `https://gitlab.com`.

## Authentication

This MCP server supports two authentication methods:

### Method 1: Personal Access Token (Recommended for most users)

1. Create a GitLab Personal Access Token:
   - Go to GitLab → User Settings → Access Tokens
   - Create a token with `read_api` scope (minimum required)

2. Set the `GITLAB_TOKEN` environment variable to your token value

### Method 2: OAuth2 Token (For OAuth2 applications)

1. If you have an OAuth2 token from a GitLab OAuth2 application flow
2. Set the `GITLAB_OAUTH_TOKEN` environment variable to your OAuth2 token value

**To create an OAuth2 application:**
1. Go to GitLab → User Settings → Applications
2. Create a new application with appropriate scopes (`read_api` minimum)
3. Use the OAuth2 flow to obtain an access token
4. Use that token as `GITLAB_OAUTH_TOKEN`

### Environment Variables

- **`GITLAB_TOKEN`** - Your GitLab Personal Access Token (if using personal token auth)
- **`GITLAB_OAUTH_TOKEN`** - Your GitLab OAuth2 Token (if using OAuth2 auth)
- **`GITLAB_URL`** - GitLab instance URL (defaults to `https://gitlab.com`)

**Note:** The server will first check for `GITLAB_OAUTH_TOKEN`, and if not found, will use `GITLAB_TOKEN`. You only need to set one of these.

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
uv run python -m mcp_gitlab_server
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
        "--from", "/path/to/your/gitlab-mcp-server/dist/mcp_gitlab_server-0.1.0-py3-none-any.whl",
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
uv run python -m mcp_gitlab_server
```
