import os
from datetime import datetime, timedelta
from typing import Annotated, Any

import gitlab
import gitlab.exceptions
from mcp.server.fastmcp import FastMCP
from pydantic import Field

__version__ = "0.0.4"

server = FastMCP(
    "GitLab MCP Server", dependencies=["python-gitlab"], version=__version__
)

# Global variable to store GitLab client
_gl_client: gitlab.Gitlab | None = None


def get_gitlab_client() -> gitlab.Gitlab:
    """Get or create GitLab client with OAuth2 or Personal Access Token authentication."""
    global _gl_client

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
    """List GitLab projects accessible to the authenticated user."""
    try:
        gl = get_gitlab_client()
        per_page = min(per_page, 100)

        projects = gl.projects.list(
            owned=owned,
            starred=starred,
            per_page=per_page,
            all=False,
        )

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
    """List GitLab groups accessible to the authenticated user."""
    try:
        gl = get_gitlab_client()
        per_page = min(per_page, 100)

        groups = gl.groups.list(
            owned=owned,
            per_page=per_page,
            all=False,
        )

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
    """List all projects within a specific GitLab group."""
    try:
        gl = get_gitlab_client()
        group = gl.groups.get(group_id)
        per_page = min(per_page, 100)

        projects = group.projects.list(
            per_page=per_page,
            all=False,
        )

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
    """Get information about the authenticated user."""
    try:
        gl = get_gitlab_client()
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
    """Search for GitLab repositories by name, description, or keywords."""
    try:
        gl = get_gitlab_client()
        per_page = min(per_page, 100)

        projects = gl.projects.list(
            search=search,
            per_page=per_page,
            all=False,
        )

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
    """Get detailed information about a specific GitLab repository."""
    try:
        gl = get_gitlab_client()
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


@server.tool()
def read_repository_code(
    project_id: Annotated[
        int | str,
        Field(description="The project ID or path (e.g., 'username/repo-name')"),
    ],
    ref: Annotated[str, Field(description="Branch, tag, or commit SHA")] = "main",
    path: Annotated[
        str, Field(description="Specific directory path to read (leave empty for root)")
    ] = "",
    max_files: Annotated[
        int, Field(description="Maximum number of files to read (default: 50)")
    ] = 50,
    max_file_size: Annotated[
        int, Field(description="Maximum file size in bytes to read (default: 100KB)")
    ] = 100 * 1024,
    include_patterns: Annotated[
        str,
        Field(
            description="Comma-separated file patterns to include (e.g., '*.py,*.js')"
        ),
    ] = "",
    exclude_patterns: Annotated[
        str,
        Field(
            description="Comma-separated file patterns to exclude (e.g., '*.log,*.tmp')"
        ),
    ] = "*.log,*.tmp,*.lock,node_modules/*,__pycache__/*,*.pyc,*.pyo,*.pyd,.git/*",
) -> str | dict[str, Any]:
    """Read the complete code structure and content of a repository with filtering options."""
    import fnmatch

    try:
        gl = get_gitlab_client()
        project = gl.projects.get(project_id)

        include_list = [p.strip() for p in include_patterns.split(",") if p.strip()]
        exclude_list = [p.strip() for p in exclude_patterns.split(",") if p.strip()]

        def should_include_file(file_path: str) -> bool:
            """Check if file should be included based on patterns."""
            for pattern in exclude_list:
                if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(
                    file_path.lower(), pattern.lower()
                ):
                    return False

            if include_list:
                return any(
                    fnmatch.fnmatch(file_path, pattern)
                    or fnmatch.fnmatch(file_path.lower(), pattern.lower())
                    for pattern in include_list
                )

            return True

        def traverse_tree(
            current_path: str = "", level: int = 0
        ) -> list[dict[str, Any]]:
            """Recursively traverse repository tree."""
            if level > 10:
                return []

            try:
                tree_items = project.repository_tree(
                    path=current_path, ref=ref, get_all=True
                )
                files_data = []
                files_processed = 0

                for item in tree_items:
                    if files_processed >= max_files:
                        break

                    item_path = item["path"]
                    item_name = item["name"]
                    item_type = item["type"]

                    if item_type == "tree":
                        subdirectory_files = traverse_tree(item_path, level + 1)
                        files_data.extend(subdirectory_files)
                        files_processed += len(subdirectory_files)

                    elif item_type == "blob":
                        if not should_include_file(item_path):
                            continue

                        try:
                            headers = project.files.head(item_path, ref=ref)
                            file_size = int(headers.get("X-Gitlab-Size", 0))

                            file_info = {
                                "path": item_path,
                                "name": item_name,
                                "type": "file",
                                "size": file_size,
                                "id": item["id"],
                            }

                            if file_size <= max_file_size:
                                try:
                                    file_obj = project.files.get(
                                        file_path=item_path, ref=ref
                                    )
                                    try:
                                        content: str = str(file_obj.decode())
                                        file_info["content"] = content
                                        file_info["encoding"] = "utf-8"
                                    except UnicodeDecodeError:
                                        file_info["content"] = "[Binary file]"
                                        file_info["encoding"] = "binary"

                                except Exception as e:
                                    file_info["content"] = (
                                        f"[Error reading file: {str(e)}]"
                                    )
                                    file_info["encoding"] = "error"
                            else:
                                file_info["content"] = (
                                    f"[File too large: {file_size} bytes]"
                                )
                                file_info["encoding"] = "skipped"

                            files_data.append(file_info)
                            files_processed += 1

                        except Exception as e:
                            files_data.append(
                                {
                                    "path": item_path,
                                    "name": item_name,
                                    "type": "file",
                                    "size": 0,
                                    "id": item["id"],
                                    "content": f"[Error accessing file: {str(e)}]",
                                    "encoding": "error",
                                }
                            )
                            files_processed += 1

                return files_data

            except Exception as e:
                return [{"error": f"Error traversing path '{current_path}': {str(e)}"}]

        repository_files = traverse_tree(path)

        repo_info = {
            "project_id": project.id,
            "project_name": project.name,
            "project_path": project.path_with_namespace,
            "ref": ref,
            "path": path if path else "/",
            "total_files": len(repository_files),
            "max_files_limit": max_files,
            "max_file_size_limit": max_file_size,
            "include_patterns": include_patterns if include_patterns else "all files",
            "exclude_patterns": exclude_patterns,
            "files": repository_files,
        }

        return repo_info

    except Exception as e:
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            return f"Repository not found or access denied: {str(e)}"
        elif "authentication" in str(e).lower():
            return "GitLab authentication failed. Please check your GITLAB_TOKEN or GITLAB_OAUTH_TOKEN."
        else:
            return f"GitLab connection error: {str(e)}"


@server.tool()
def read_repository_file(
    project_id: Annotated[
        int | str,
        Field(description="The project ID or path (e.g., 'username/repo-name')"),
    ],
    file_path: Annotated[str, Field(description="Path to the file to read")],
    ref: Annotated[str, Field(description="Branch, tag, or commit SHA")] = "main",
) -> str | dict[str, Any]:
    """Read the content of a specific file from a GitLab repository."""
    try:
        gl = get_gitlab_client()
        project = gl.projects.get(project_id)

        file_obj = project.files.get(file_path=file_path, ref=ref)
        headers = project.files.head(file_path, ref=ref)
        file_size = int(headers.get("X-Gitlab-Size", 0))

        try:
            content: str = str(file_obj.decode())
            encoding = "utf-8"
        except UnicodeDecodeError:
            encoding = "binary"
            content = "[Binary file - cannot display content]"

        return {
            "project_id": project.id,
            "project_name": project.name,
            "project_path": project.path_with_namespace,
            "file_path": file_path,
            "ref": ref,
            "size": file_size,
            "encoding": encoding,
            "content": content,
            "last_commit_id": file_obj.last_commit_id,
            "file_name": file_obj.file_name,
        }

    except Exception as e:
        if "not found" in str(e).lower() or "404" in str(e):
            return f"File not found: {file_path} in {project_id} at ref {ref}"
        elif "access denied" in str(e).lower():
            return f"Access denied to file: {file_path} in {project_id}"
        elif "authentication" in str(e).lower():
            return "GitLab authentication failed. Please check your GITLAB_TOKEN or GITLAB_OAUTH_TOKEN."
        else:
            return f"Error reading file: {str(e)}"


@server.tool()
def list_merge_requests(
    project_id: Annotated[
        int | str,
        Field(description="The project ID or path (e.g., 'username/repo-name')"),
    ],
    state: Annotated[
        str, Field(description="State of merge requests (opened, closed, merged, all)")
    ] = "all",
    per_page: Annotated[
        int, Field(description="Number of merge requests to return (max 100)")
    ] = 50,
    order_by: Annotated[
        str, Field(description="Order by field (created_at, updated_at, title)")
    ] = "created_at",
    sort: Annotated[str, Field(description="Sort order (asc, desc)")] = "desc",
) -> str | list[dict[str, Any]]:
    """List merge requests for a GitLab repository."""
    try:
        gl = get_gitlab_client()
        project = gl.projects.get(project_id)
        per_page = min(per_page, 100)

        mrs = project.mergerequests.list(
            state=state,
            per_page=per_page,
            order_by=order_by,
            sort=sort,
            all=False,
        )

        mr_data: list[dict[str, Any]] = []
        for mr in mrs:
            mr_info = {
                "iid": mr.iid,
                "id": mr.id,
                "title": mr.title,
                "description": mr.description,
                "state": mr.state,
                "created_at": mr.created_at,
                "updated_at": mr.updated_at,
                "merged_at": getattr(mr, "merged_at", None),
                "closed_at": getattr(mr, "closed_at", None),
                "author": {
                    "id": mr.author["id"],
                    "name": mr.author["name"],
                    "username": mr.author["username"],
                },
                "source_branch": mr.source_branch,
                "target_branch": mr.target_branch,
                "web_url": mr.web_url,
                "merge_status": getattr(mr, "merge_status", None),
                "has_conflicts": getattr(mr, "has_conflicts", False),
                "assignees": [
                    {
                        "id": assignee["id"],
                        "name": assignee["name"],
                        "username": assignee["username"],
                    }
                    for assignee in (getattr(mr, "assignees", None) or [])
                ],
                "reviewers": [
                    {
                        "id": reviewer["id"],
                        "name": reviewer["name"],
                        "username": reviewer["username"],
                    }
                    for reviewer in (getattr(mr, "reviewers", None) or [])
                ],
                "labels": getattr(mr, "labels", []),
                "upvotes": getattr(mr, "upvotes", 0),
                "downvotes": getattr(mr, "downvotes", 0),
                "user_notes_count": getattr(mr, "user_notes_count", 0),
            }
            mr_data.append(mr_info)

        return mr_data

    except Exception as e:
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            return f"Repository not found or access denied: {str(e)}"
        elif "authentication" in str(e).lower():
            return "GitLab authentication failed. Please check your GITLAB_TOKEN or GITLAB_OAUTH_TOKEN."
        else:
            return f"GitLab connection error: {str(e)}"


@server.tool()
def get_merge_request_analytics(
    project_id: Annotated[
        int | str,
        Field(description="The project ID or path (e.g., 'username/repo-name')"),
    ],
    days_back: Annotated[
        int, Field(description="Number of days back to analyze (default: 90)")
    ] = 90,
    per_page: Annotated[
        int, Field(description="Number of merge requests to fetch per page (max 100)")
    ] = 100,
) -> str | dict[str, Any]:
    """Calculate merge request lifetime analytics for a GitLab repository."""
    try:
        gl = get_gitlab_client()
        project = gl.projects.get(project_id)

        from_date = datetime.now() - timedelta(days=days_back)

        all_mrs = []
        page = 1
        max_pages = 10

        while page <= max_pages:
            mrs = project.mergerequests.list(
                state="merged",
                per_page=min(per_page, 100),
                page=page,
                order_by="created_at",
                sort="desc",
            )

            if not mrs:
                break

            mrs_list = list(mrs)

            for mr in mrs_list:
                try:
                    created_date = datetime.fromisoformat(
                        mr.created_at.replace("Z", "+00:00")
                    )
                    if created_date < from_date:
                        break
                    all_mrs.append(mr)
                except (ValueError, AttributeError):
                    continue

            if len(mrs_list) < per_page or (
                len(mrs_list) > 0
                and datetime.fromisoformat(
                    mrs_list[-1].created_at.replace("Z", "+00:00")
                )
                < from_date
            ):
                break

            page += 1

        lifetimes_hours = []
        lifetimes_days = []
        mr_details = []

        for mr in all_mrs:
            try:
                created_at = datetime.fromisoformat(
                    mr.created_at.replace("Z", "+00:00")
                )
                merged_at = datetime.fromisoformat(mr.merged_at.replace("Z", "+00:00"))

                lifetime_delta = merged_at - created_at
                lifetime_hours = lifetime_delta.total_seconds() / 3600
                lifetime_days = lifetime_hours / 24

                lifetimes_hours.append(lifetime_hours)
                lifetimes_days.append(lifetime_days)

                mr_details.append(
                    {
                        "iid": mr.iid,
                        "title": mr.title,
                        "created_at": mr.created_at,
                        "merged_at": mr.merged_at,
                        "lifetime_hours": round(lifetime_hours, 2),
                        "lifetime_days": round(lifetime_days, 2),
                        "author": mr.author["name"],
                        "web_url": mr.web_url,
                    }
                )

            except (ValueError, AttributeError, TypeError):
                continue

        if not lifetimes_hours:
            return {
                "project_id": project.id,
                "project_name": project.name,
                "project_path": project.path_with_namespace,
                "analysis_period_days": days_back,
                "total_merged_mrs": 0,
                "message": "No merged merge requests found in the specified time period.",
            }

        total_mrs = len(lifetimes_hours)
        avg_lifetime_hours = sum(lifetimes_hours) / total_mrs
        avg_lifetime_days = avg_lifetime_hours / 24
        min_lifetime_hours = min(lifetimes_hours)
        max_lifetime_hours = max(lifetimes_hours)

        sorted_lifetimes = sorted(lifetimes_hours)
        median_lifetime_hours = (
            sorted_lifetimes[total_mrs // 2]
            if total_mrs % 2 == 1
            else (
                sorted_lifetimes[total_mrs // 2 - 1] + sorted_lifetimes[total_mrs // 2]
            )
            / 2
        )

        def percentile(data, p):
            """Calculate percentile value for given data and percentage."""
            n = len(data)
            index = (p / 100) * (n - 1)
            if index.is_integer():
                return data[int(index)]
            else:
                lower = data[int(index)]
                upper = data[int(index) + 1]
                return lower + (upper - lower) * (index - int(index))

        p25_hours = percentile(sorted_lifetimes, 25)
        p75_hours = percentile(sorted_lifetimes, 75)
        p90_hours = percentile(sorted_lifetimes, 90)

        return {
            "project_id": project.id,
            "project_name": project.name,
            "project_path": project.path_with_namespace,
            "analysis_period_days": days_back,
            "total_merged_mrs": total_mrs,
            "statistics": {
                "average_lifetime": {
                    "hours": round(avg_lifetime_hours, 2),
                    "days": round(avg_lifetime_days, 2),
                },
                "median_lifetime": {
                    "hours": round(median_lifetime_hours, 2),
                    "days": round(median_lifetime_hours / 24, 2),
                },
                "min_lifetime": {
                    "hours": round(min_lifetime_hours, 2),
                    "days": round(min_lifetime_hours / 24, 2),
                },
                "max_lifetime": {
                    "hours": round(max_lifetime_hours, 2),
                    "days": round(max_lifetime_hours / 24, 2),
                },
                "percentiles": {
                    "25th": {
                        "hours": round(p25_hours, 2),
                        "days": round(p25_hours / 24, 2),
                    },
                    "75th": {
                        "hours": round(p75_hours, 2),
                        "days": round(p75_hours / 24, 2),
                    },
                    "90th": {
                        "hours": round(p90_hours, 2),
                        "days": round(p90_hours / 24, 2),
                    },
                },
            },
            "sample_merge_requests": mr_details[:10],
            "all_merge_requests": mr_details,
        }

    except Exception as e:
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            return f"Repository not found or access denied: {str(e)}"
        elif "authentication" in str(e).lower():
            return "GitLab authentication failed. Please check your GITLAB_TOKEN or GITLAB_OAUTH_TOKEN."
        else:
            return f"GitLab connection error: {str(e)}"


def main():
    """Run the MCP GitLab server."""
    server.run()


if __name__ == "__main__":
    main()
