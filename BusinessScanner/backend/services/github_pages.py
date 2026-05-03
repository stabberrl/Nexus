"""GitHub Pages publishing service.

Automatically publishes generated sites to GitHub Pages
upon payment confirmation via the GitHub REST API.
"""

import requests
from typing import Optional
from pathlib import Path

class GitHubPagesService:
    """Service for publishing to GitHub Pages via REST API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, github_token: str, github_user: str) -> None:
        self.github_token = github_token
        self.github_user = github_user
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        })

    def create_repo_and_publish(
        self, repo_name: str, site_path: str
    ) -> Optional[str]:
        """Create a GitHub repo and publish the site.

        Args:
            repo_name: Repository name (usually business slug)
            site_path: Local path to generated site files

        Returns:
            Published URL or None on failure
        """
        if not self.github_token:
            print("GitHub token not configured")
            return None

        try:
            # Create repo
            resp = self.session.post(
                f"{self.BASE_URL}/user/repos",
                json={"name": repo_name, "auto_init": True, "private": False},
                timeout=15,
            )
            if resp.status_code not in (201, 422):  # 422 = already exists
                resp.raise_for_status()

            # Upload index.html
            site_dir = Path(site_path)
            index_file = site_dir / "index.html"
            if index_file.exists():
                content = index_file.read_text(encoding="utf-8")
                import base64
                encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
                
                self.session.put(
                    f"{self.BASE_URL}/repos/{self.github_user}/{repo_name}/contents/index.html",
                    json={
                        "message": "Add generated site index.html",
                        "content": encoded,
                    },
                    timeout=15,
                )

            # Activate GitHub Pages
            self.session.post(
                f"{self.BASE_URL}/repos/{self.github_user}/{repo_name}/pages",
                json={"source": {"branch": "main"}},
                timeout=15,
            )

            published_url = f"https://{self.github_user}.github.io/{repo_name}"
            return published_url
        except Exception as e:
            print(f"GitHub Pages publish error: {e}")
            return None
