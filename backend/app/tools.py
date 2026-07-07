"""
tools.py — functions the LLM agent can choose to call on its own.

Right now there's just one: pulling Minali's latest public GitHub repos
live, so the chatbot's answers about "recent" or "latest" work stay
accurate without needing to manually edit about_me.md every time.
"""
import os
import requests

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "mina-li2")


def get_latest_repos(limit: int = 5) -> str:
    """Fetches the most recently updated public repos for GITHUB_USERNAME
    from the GitHub API (no auth needed for public data, but rate-limited
    to 60 requests/hour per IP without a token)."""
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
    params = {"sort": "updated", "per_page": limit}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        repos = response.json()
    except requests.RequestException as e:
        return f"Error fetching GitHub repos: {e}"

    if not repos:
        return "No public repositories found."

    lines = []
    for repo in repos:
        name = repo.get("name")
        description = repo.get("description") or "No description provided"
        updated = repo.get("updated_at", "")[:10]
        url_ = repo.get("html_url")
        lines.append(f"- {name}: {description} (last updated {updated}) — {url_}")

    return "\n".join(lines)