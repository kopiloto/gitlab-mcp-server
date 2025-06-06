import os
from typing import Annotated, Any

import gitlab
import gitlab.exceptions
from mcp.server.fastmcp import FastMCP
from pydantic import Field

__version__ = "0.0.2"

server = FastMCP(
    "GitLab MCP Server", dependencies=["python-gitlab"], version=__version__
)

# Global variable to store GitLab client
_gl_client: gitlab.Gitlab | None = None


def get_gitlab_client() -> gitlab.Gitlab:
    """Get or create GitLab client with support for both Personal Access Token and OAuth2 authentication"""
    global _gl_client

    # Try OAuth2 token first
    oauth_token = os.getenv("GITLAB_OAUTH_TOKEN")
    personal_token = os.getenv("GITLAB_TOKEN")

    if not oauth_token and not personal_token:
        raise ValueError(
            "You must set either GITLAB_OAUTH_TOKEN or GITLAB_TOKEN environment variable to use this tool"
        )

    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")

    # Create new client if not exists or token changed
    if _gl_client is None:
        if oauth_token:
            # Use OAuth2 token authentication
            _gl_client = gitlab.Gitlab(gitlab_url, oauth_token=oauth_token)
        else:
            # Use personal access token authentication
            _gl_client = gitlab.Gitlab(gitlab_url, private_token=personal_token)

        _gl_client.auth()

    return _gl_client


@server.tool()
def list_projects(
    owned: Annotated[
        bool, Field(description="Only list projects owned by the authenticated user")
    ] = False,
    starred: Annotated[bool, Field(description="Only list starred projects")] = False,
    per_page: Annotated[
        int, Field(description="Number of projects to return (max 100)")
    ] = 20,
) -> str | list[dict[str, Any]]:
    """
    List GitLab projects accessible to the authenticated user.
    """
    try:
        gl = get_gitlab_client()

        # Limit per_page to prevent overwhelming responses
        per_page = min(per_page, 100)

        projects = gl.projects.list(
            owned=owned,
            starred=starred,
            per_page=per_page,
            all=False,  # Don't fetch all pages to keep response manageable
        )

        # Return simplified project data
        project_data: list[dict[str, Any]] = []
        for project in projects:
            project_data.append(
                {
                    "id": project.id,
                    "name": project.name,
                    "path": project.path,
                    "path_with_namespace": project.path_with_namespace,
                    "description": project.description,
                    "web_url": project.web_url,
                    "visibility": project.visibility,
                    "default_branch": getattr(project, "default_branch", None),
                    "created_at": project.created_at,
                    "last_activity_at": project.last_activity_at,
                }
            )

        return project_data
    except gitlab.exceptions.GitlabAuthenticationError:
        return "GitLab authentication failed. Please check your GITLAB_TOKEN or GITLAB_OAUTH_TOKEN."
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"GitLab connection error: {str(e)}"


@server.tool()
def list_groups(
    owned: Annotated[
        bool, Field(description="Only list groups owned by the authenticated user")
    ] = False,
    per_page: Annotated[
        int, Field(description="Number of groups to return (max 100)")
    ] = 20,
) -> str | list[dict[str, Any]]:
    """
    List GitLab groups accessible to the authenticated user.
    """
    try:
        gl = get_gitlab_client()

        # Limit per_page to prevent overwhelming responses
        per_page = min(per_page, 100)

        groups = gl.groups.list(
            owned=owned,
            per_page=per_page,
            all=False,  # Don't fetch all pages to keep response manageable
        )

        # Return simplified group data
        group_data: list[dict[str, Any]] = []
        for group in groups:
            group_data.append(
                {
                    "id": group.id,
                    "name": group.name,
                    "path": group.path,
                    "full_path": group.full_path,
                    "description": group.description,
                    "web_url": group.web_url,
                    "visibility": group.visibility,
                    "project_count": getattr(group, "project_count", 0),
                    "subgroup_count": getattr(group, "subgroup_count", 0),
                    "created_at": group.created_at,
                }
            )

        return group_data
    except gitlab.exceptions.GitlabAuthenticationError:
        return "GitLab authentication failed. Please check your GITLAB_TOKEN or GITLAB_OAUTH_TOKEN."
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"GitLab connection error: {str(e)}"


@server.tool()
def list_group_projects(
    group_id: Annotated[int | str, Field(description="The group ID or path")],
    per_page: Annotated[
        int, Field(description="Number of projects to return (max 100)")
    ] = 20,
) -> str | list[dict[str, Any]]:
    """
    List all projects within a specific GitLab group.
    """
    try:
        gl = get_gitlab_client()

        # Get the group
        group = gl.groups.get(group_id)

        # Limit per_page to prevent overwhelming responses
        per_page = min(per_page, 100)

        # Get projects in the group
        projects = group.projects.list(
            per_page=per_page,
            all=False,  # Don't fetch all pages to keep response manageable
        )

        # Return simplified project data
        project_data: list[dict[str, Any]] = []
        for project in projects:
            project_data.append(
                {
                    "id": project.id,
                    "name": project.name,
                    "path": project.path,
                    "path_with_namespace": project.path_with_namespace,
                    "description": project.description,
                    "web_url": project.web_url,
                    "visibility": project.visibility,
                    "default_branch": getattr(project, "default_branch", None),
                    "created_at": project.created_at,
                    "last_activity_at": project.last_activity_at,
                }
            )

        return project_data
    except Exception as e:
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            return f"Group not found or access denied: {str(e)}"
        elif "authentication" in str(e).lower():
            return "GitLab authentication failed. Please check your GITLAB_TOKEN or GITLAB_OAUTH_TOKEN."
        else:
            return f"GitLab connection error: {str(e)}"


@server.tool()
def get_user_info() -> str | dict[str, Any]:
    """
    Get information about the authenticated user.
    """
    try:
        gl = get_gitlab_client()

        # Get current user info
        user = gl.user
        if user is None:
            return "Could not retrieve user information"

        return {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "email": getattr(user, "email", None),
            "web_url": user.web_url,
            "avatar_url": getattr(user, "avatar_url", None),
            "created_at": user.created_at,
            "is_admin": getattr(user, "is_admin", False),
            "bio": getattr(user, "bio", None),
            "location": getattr(user, "location", None),
            "public_email": getattr(user, "public_email", None),
        }
    except gitlab.exceptions.GitlabAuthenticationError:
        return "GitLab authentication failed. Please check your GITLAB_TOKEN or GITLAB_OAUTH_TOKEN."
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"GitLab connection error: {str(e)}"


@server.tool()
def search_repositories(
    search: Annotated[
        str,
        Field(
            description="Search term to find repositories by name, description, or content"
        ),
    ],
    per_page: Annotated[
        int, Field(description="Number of repositories to return (max 100)")
    ] = 20,
) -> str | list[dict[str, Any]]:
    """
    Search for GitLab repositories by name, description, or keywords.
    """
    try:
        gl = get_gitlab_client()

        # Limit per_page to prevent overwhelming responses
        per_page = min(per_page, 100)

        # Search for projects
        projects = gl.projects.list(
            search=search,
            per_page=per_page,
            all=False,  # Don't fetch all pages to keep response manageable
        )

        # Return simplified project data
        project_data: list[dict[str, Any]] = []
        for project in projects:
            project_data.append(
                {
                    "id": project.id,
                    "name": project.name,
                    "path": project.path,
                    "path_with_namespace": project.path_with_namespace,
                    "description": project.description,
                    "web_url": project.web_url,
                    "visibility": project.visibility,
                    "default_branch": getattr(project, "default_branch", None),
                    "created_at": project.created_at,
                    "last_activity_at": project.last_activity_at,
                    "stars_count": getattr(project, "star_count", 0),
                    "forks_count": getattr(project, "forks_count", 0),
                }
            )

        return project_data
    except gitlab.exceptions.GitlabAuthenticationError:
        return "GitLab authentication failed. Please check your GITLAB_TOKEN or GITLAB_OAUTH_TOKEN."
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"GitLab connection error: {str(e)}"


@server.tool()
def get_repository_details(
    project_id: Annotated[
        int | str,
        Field(description="The project ID or path (e.g., 'username/repo-name')"),
    ],
) -> str | dict[str, Any]:
    """
    Get detailed information about a specific GitLab repository.
    """
    try:
        gl = get_gitlab_client()

        # Get the project
        project = gl.projects.get(project_id)

        # Get additional details
        languages: dict[str, Any] = {}
        try:
            lang_result = project.languages()
            if isinstance(lang_result, dict):
                languages = lang_result
        except Exception:
            # Some projects might not have language data
            pass

        # Get branches count
        branches_count = 0
        try:
            branches_count = len(project.branches.list(all=True))
        except Exception:
            pass

        # Get tags count
        tags_count = 0
        try:
            tags_count = len(project.tags.list(all=True))
        except Exception:
            pass

        return {
            "id": project.id,
            "name": project.name,
            "path": project.path,
            "path_with_namespace": project.path_with_namespace,
            "description": project.description,
            "web_url": project.web_url,
            "ssh_url_to_repo": getattr(project, "ssh_url_to_repo", None),
            "http_url_to_repo": getattr(project, "http_url_to_repo", None),
            "visibility": project.visibility,
            "default_branch": getattr(project, "default_branch", None),
            "created_at": project.created_at,
            "last_activity_at": project.last_activity_at,
            "avatar_url": getattr(project, "avatar_url", None),
            "star_count": getattr(project, "star_count", 0),
            "forks_count": getattr(project, "forks_count", 0),
            "open_issues_count": getattr(project, "open_issues_count", 0),
            "readme_url": getattr(project, "readme_url", None),
            "license": getattr(project, "license", {}).get("name")
            if getattr(project, "license", None)
            else None,
            "languages": languages,
            "branches_count": branches_count,
            "tags_count": tags_count,
            "size": getattr(project, "repository_size", 0),
            "archived": getattr(project, "archived", False),
            "issues_enabled": getattr(project, "issues_enabled", False),
            "merge_requests_enabled": getattr(project, "merge_requests_enabled", False),
            "wiki_enabled": getattr(project, "wiki_enabled", False),
            "snippets_enabled": getattr(project, "snippets_enabled", False),
            "container_registry_enabled": getattr(
                project, "container_registry_enabled", False
            ),
            "namespace": {
                "id": project.namespace.get("id"),
                "name": project.namespace.get("name"),
                "path": project.namespace.get("path"),
                "kind": project.namespace.get("kind"),
            }
            if hasattr(project, "namespace") and project.namespace
            else None,
        }
    except Exception as e:
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            return f"Repository not found or access denied: {str(e)}"
        elif "authentication" in str(e).lower():
            return "GitLab authentication failed. Please check your GITLAB_TOKEN or GITLAB_OAUTH_TOKEN."
        else:
            return f"GitLab connection error: {str(e)}"


def main():
    server.run()


if __name__ == "__main__":
    main()
