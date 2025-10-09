from __future__ import annotations
import frappe, json, time, base64, hmac, hashlib
import requests
from typing import Dict, Any

GITHUB_API = "https://api.github.com"

class GitHub:
    def __init__(self):
        s = frappe.get_single("LD GitHub Settings")
        self.auth_type = s.auth_type
        self.pat = s.pat
        if not self.pat:
            frappe.throw("GitHub PAT not configured in LD GitHub Settings")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.pat}",
            "Accept": "application/vnd.github+json"
        })

    def create_branch(self, repo: str, new_branch: str, from_branch: str) -> str:
        # get sha of from_branch
        r = self.session.get(f"{GITHUB_API}/repos/{repo}/git/ref/heads/{from_branch}")
        r.raise_for_status()
        sha = r.json()["object"]["sha"]
        r = self.session.post(f"{GITHUB_API}/repos/{repo}/git/refs", json={
            "ref": f"refs/heads/{new_branch}", "sha": sha
        })
        r.raise_for_status()
        return new_branch

    def upsert_files(self, repo: str, branch: str, files: Dict[str, str], message: str):
        # naive approach: PUT per file via contents API
        for path, content in files.items():
            # get current sha (if exists)
            get = self.session.get(f"{GITHUB_API}/repos/{repo}/contents/{path}", params={"ref": branch})
            sha = get.json().get("sha") if get.status_code == 200 else None
            put = self.session.put(
                f"{GITHUB_API}/repos/{repo}/contents/{path}",
                json={
                    "message": message,
                    "content": base64.b64encode(content.encode()).decode(),
                    "branch": branch,
                    **({"sha": sha} if sha else {})
                },
            )
            put.raise_for_status()

    def open_pr(self, repo: str, title: str, head: str, base: str) -> str:
        r = self.session.post(f"{GITHUB_API}/repos/{repo}/pulls", json={
            "title": title, "head": head, "base": base
        })
        r.raise_for_status()
        return r.json()["html_url"]
