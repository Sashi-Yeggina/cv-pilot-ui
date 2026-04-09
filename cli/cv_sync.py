"""
cv_sync.py — GitHub cloud sync for CV Pilot
--------------------------------------------
Pushes aligned CVs + the index to a private GitHub repo so your
whole sales team can access the latest CV library at any time.

Requires:
  - A GitHub Personal Access Token (classic) with repo scope
  - A private GitHub repo (e.g. sashi-cv-library)

Set in .env:
  GITHUB_TOKEN=ghp_...
  GITHUB_REPO=your-username/sashi-cv-library
"""

import os, base64, json, hashlib
from pathlib import Path
from datetime import datetime

try:
    import requests
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

console = Console() if HAS_DEPS else None

GITHUB_API = "https://api.github.com"


# ── Config helpers ────────────────────────────────────────────────────────────

def _load_env(script_dir: str) -> dict:
    env = {}
    env_file = Path(script_dir) / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    # OS env takes priority
    for k in ("GITHUB_TOKEN", "GITHUB_REPO"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def _headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# ── Core GitHub API operations ────────────────────────────────────────────────

def _get_file_sha(token: str, repo: str, path: str) -> str | None:
    """Returns current SHA of a file in the repo, or None if it doesn't exist."""
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}"
    r = requests.get(url, headers=_headers(token))
    if r.status_code == 200:
        return r.json().get("sha")
    return None


def _push_file(token: str, repo: str, path: str, content_bytes: bytes, message: str) -> bool:
    """Create or update a file in the GitHub repo."""
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}"
    sha = _get_file_sha(token, repo, path)
    payload = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode(),
        "committer": {
            "name": "CV Pilot Bot",
            "email": "cv-pilot@noreply.github.com"
        }
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=_headers(token), json=payload)
    return r.status_code in (200, 201)


def _pull_file(token: str, repo: str, path: str) -> bytes | None:
    """Download a file from the GitHub repo."""
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}"
    r = requests.get(url, headers=_headers(token))
    if r.status_code == 200:
        return base64.b64decode(r.json()["content"])
    return None


def _list_folder(token: str, repo: str, folder: str = "cvs") -> list:
    """List files in a folder in the repo."""
    url = f"{GITHUB_API}/repos/{repo}/contents/{folder}"
    r = requests.get(url, headers=_headers(token))
    if r.status_code == 200:
        return r.json()  # list of {name, path, sha, download_url, ...}
    return []


def _ensure_repo_exists(token: str, repo: str) -> bool:
    """Check repo is accessible."""
    url = f"{GITHUB_API}/repos/{repo}"
    r = requests.get(url, headers=_headers(token))
    return r.status_code == 200


def _create_repo_if_needed(token: str, repo_name: str) -> str | None:
    """Create a private repo if it doesn't exist. Returns full repo path."""
    url = f"{GITHUB_API}/user/repos"
    payload = {
        "name": repo_name,
        "private": True,
        "description": "CV Pilot — shared CV library for the sales team",
        "auto_init": True,
    }
    r = requests.post(url, headers=_headers(token), json=payload)
    if r.status_code in (200, 201):
        return r.json()["full_name"]
    if r.status_code == 422:
        # Already exists — get the current user to build full name
        me = requests.get(f"{GITHUB_API}/user", headers=_headers(token)).json()
        return f"{me['login']}/{repo_name}"
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  Public interface
# ══════════════════════════════════════════════════════════════════════════════

class CVSync:
    """
    GitHub-backed cloud sync for CV Pilot.

    Usage:
        sync = CVSync()
        sync.push_cv("aligned_cvs/AWS_Cloud_Engineer_20260406.docx")
        sync.push_index("cv_index.json")
        sync.pull_all(local_dir="aligned_cvs/")
    """

    def __init__(self, script_dir: str = "."):
        if not HAS_DEPS:
            raise ImportError("Run: pip install requests rich")
        env = _load_env(script_dir)
        self.token = env.get("GITHUB_TOKEN", "")
        self.repo  = env.get("GITHUB_REPO", "")
        self.enabled = bool(self.token and self.repo)

    # ── Push a single aligned CV ───────────────────────────────────────────────
    def push_cv(self, local_path: str, role_category: str = "", date: str = "") -> bool:
        if not self.enabled:
            return False
        name = Path(local_path).name
        remote_path = f"cvs/{name}"
        content = Path(local_path).read_bytes()
        date_str = date or datetime.now().strftime("%Y-%m-%d")
        msg = f"Add CV: {name} [{date_str}]"
        if role_category:
            msg = f"Add {role_category} CV: {name} [{date_str}]"
        ok = _push_file(self.token, self.repo, remote_path, content, msg)
        if ok:
            console.print(f"[green]☁  Pushed to GitHub:[/] {remote_path}")
        else:
            console.print(f"[yellow]⚠  Could not push {name} to GitHub[/]")
        return ok

    # ── Push the index file ────────────────────────────────────────────────────
    def push_index(self, index_path: str = "cv_index.json") -> bool:
        if not self.enabled:
            return False
        content = Path(index_path).read_bytes()
        ok = _push_file(self.token, self.repo, "cv_index.json", content,
                        f"Update CV index [{datetime.now().strftime('%Y-%m-%d %H:%M')}]")
        if ok:
            console.print("[green]☁  Index synced to GitHub[/]")
        return ok

    # ── Pull latest index from GitHub ──────────────────────────────────────────
    def pull_index(self, local_path: str = "cv_index.json") -> bool:
        if not self.enabled:
            return False
        data = _pull_file(self.token, self.repo, "cv_index.json")
        if data:
            Path(local_path).write_bytes(data)
            console.print("[green]☁  Pulled latest index from GitHub[/]")
            return True
        console.print("[yellow]No index found in GitHub repo yet[/]")
        return False

    # ── Pull all CVs from GitHub into local folder ─────────────────────────────
    def pull_all(self, local_dir: str = "aligned_cvs") -> int:
        if not self.enabled:
            return 0
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        files = _list_folder(self.token, self.repo, "cvs")
        count = 0
        with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"), transient=True) as p:
            p.add_task(f"Pulling {len(files)} CVs from GitHub...", total=None)
            for f in files:
                if f["name"].endswith(".docx"):
                    local_path = Path(local_dir) / f["name"]
                    if not local_path.exists():  # skip already-downloaded files
                        data = _pull_file(self.token, self.repo, f["path"])
                        if data:
                            local_path.write_bytes(data)
                            count += 1
        if count:
            console.print(f"[green]☁  Pulled {count} new CVs from GitHub → {local_dir}/[/]")
        else:
            console.print("[dim]All CVs already up to date locally.[/]")
        return count

    # ── List CVs in GitHub repo ────────────────────────────────────────────────
    def list_remote(self) -> list:
        if not self.enabled:
            return []
        return _list_folder(self.token, self.repo, "cvs")

    # ── Push a base CV to the base_cvs folder ─────────────────────────────────
    def push_base_cv(self, local_path: str) -> bool:
        if not self.enabled:
            return False
        name = Path(local_path).name
        remote_path = f"base_cvs/{name}"
        content = Path(local_path).read_bytes()
        ok = _push_file(self.token, self.repo, remote_path, content,
                        f"Add base CV: {name}")
        if ok:
            console.print(f"[green]☁  Base CV pushed to GitHub:[/] base_cvs/{name}")
        return ok

    # ── Pull all base CVs (for team members who need the source CVs) ───────────
    def pull_base_cvs(self, local_dir: str = "my_cvs") -> int:
        if not self.enabled:
            return 0
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        files = _list_folder(self.token, self.repo, "base_cvs")
        count = 0
        for f in files:
            if f["name"].endswith(".docx"):
                local_path = Path(local_dir) / f["name"]
                if not local_path.exists():
                    data = _pull_file(self.token, self.repo, f["path"])
                    if data:
                        local_path.write_bytes(data)
                        count += 1
        if count:
            console.print(f"[green]☁  Pulled {count} base CVs → {local_dir}/[/]")
        return count

    # ── Generate a shareable web link for a CV ─────────────────────────────────
    def get_download_url(self, filename: str) -> str | None:
        """Returns a GitHub URL that team members can use to download a specific CV."""
        if not self.enabled:
            return None
        # Raw download URL
        return f"https://raw.githubusercontent.com/{self.repo}/main/cvs/{filename}"

    # ── Status check ──────────────────────────────────────────────────────────
    def status(self) -> dict:
        if not self.enabled:
            return {"enabled": False, "reason": "GITHUB_TOKEN or GITHUB_REPO not set in .env"}
        ok = _ensure_repo_exists(self.token, self.repo)
        remote_cvs = self.list_remote() if ok else []
        return {
            "enabled": True,
            "repo": self.repo,
            "accessible": ok,
            "remote_cv_count": len(remote_cvs),
            "remote_cvs": [f["name"] for f in remote_cvs],
        }


# ══════════════════════════════════════════════════════════════════════════════
#  Standalone CLI (python cv_sync.py ...)
# ══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse, sys
    from rich.table import Table

    parser = argparse.ArgumentParser(description="CV Pilot — GitHub sync utility")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status",       help="Check GitHub connection and repo status")
    sub.add_parser("pull",         help="Pull all aligned CVs from GitHub to local")
    sub.add_parser("pull-base",    help="Pull all base CVs from GitHub to local my_cvs/")
    sub.add_parser("push-index",   help="Push cv_index.json to GitHub")
    sub.add_parser("pull-index",   help="Pull cv_index.json from GitHub")
    sub.add_parser("list",         help="List CVs in GitHub repo")
    p_push = sub.add_parser("push", help="Push a CV file to GitHub")
    p_push.add_argument("file", help="Path to the DOCX file")
    p_push.add_argument("--role", default="", help="Role category label")
    p_push_base = sub.add_parser("push-base", help="Push a base CV to GitHub")
    p_push_base.add_argument("file", help="Path to the base CV DOCX")
    p_setup = sub.add_parser("setup", help="Create the GitHub repo automatically")
    p_setup.add_argument("--name", default="sashi-cv-library", help="Repo name to create")

    args = parser.parse_args()
    sync = CVSync(script_dir=str(Path(__file__).parent))

    if args.cmd == "status":
        s = sync.status()
        if not s["enabled"]:
            console.print(f"[yellow]Sync disabled:[/] {s['reason']}")
            console.print("\nAdd to your [cyan].env[/] file:\n  GITHUB_TOKEN=ghp_...\n  GITHUB_REPO=username/repo-name")
        else:
            t = Table(show_header=False, border_style="blue")
            t.add_column("Key", style="bold cyan")
            t.add_column("Value")
            t.add_row("Repo", s["repo"])
            t.add_row("Accessible", "[green]Yes[/]" if s["accessible"] else "[red]No[/]")
            t.add_row("Remote CVs", str(s["remote_cv_count"]))
            console.print(t)
            if s["remote_cvs"]:
                console.print("\n[dim]" + "\n".join(s["remote_cvs"]) + "[/]")

    elif args.cmd == "pull":
        sync.pull_all()

    elif args.cmd == "pull-base":
        sync.pull_base_cvs()

    elif args.cmd == "push-index":
        sync.push_index()

    elif args.cmd == "pull-index":
        sync.pull_index()

    elif args.cmd == "list":
        files = sync.list_remote()
        if files:
            t = Table(title="☁  GitHub CV Library", border_style="cyan")
            t.add_column("Filename")
            t.add_column("Size")
            for f in files:
                t.add_row(f["name"], f"{f.get('size',0):,} bytes")
            console.print(t)
        else:
            console.print("[yellow]No CVs found in GitHub repo yet.[/]")

    elif args.cmd == "push" and hasattr(args, "file"):
        sync.push_cv(args.file, role_category=args.role)

    elif args.cmd == "push-base" and hasattr(args, "file"):
        sync.push_base_cv(args.file)

    elif args.cmd == "setup":
        env = _load_env(str(Path(__file__).parent))
        token = env.get("GITHUB_TOKEN", "")
        if not token:
            console.print("[red]GITHUB_TOKEN not set in .env[/]")
            sys.exit(1)
        full_name = _create_repo_if_needed(token, args.name)
        if full_name:
            console.print(f"[green]✓  Repo ready:[/] https://github.com/{full_name}")
            console.print(f"\nAdd to .env:\n  [cyan]GITHUB_REPO={full_name}[/]")
        else:
            console.print("[red]Could not create repo. Check your token has 'repo' scope.[/]")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
