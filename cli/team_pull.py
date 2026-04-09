#!/usr/bin/env python3
"""
team_pull.py — One-command setup for your sales team
-----------------------------------------------------
Each recruiter runs this ONCE to pull everything from the shared GitHub repo:
  - All aligned CVs → aligned_cvs/
  - All base CVs    → my_cvs/
  - CV index        → cv_index.json

Then they can run cv_pilot.py normally.

Usage:
  python team_pull.py
"""

import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

console = Console()

def main():
    console.print(Panel(
        "[bold cyan]CV Pilot — Team Setup[/]\n"
        "[dim]Pulling shared CV library from GitHub...[/]",
        border_style="cyan"
    ))

    try:
        from cv_sync import CVSync
    except ImportError:
        console.print("[red]cv_sync.py not found. Make sure you're in the cv_pilot folder.[/]")
        sys.exit(1)

    sync = CVSync(script_dir=str(Path(__file__).parent))

    # Check config
    status = sync.status()
    if not status["enabled"]:
        console.print(Panel(
            "[red]GitHub sync not configured.[/]\n\n"
            "Copy [cyan].env.example[/] to [cyan].env[/] and fill in:\n"
            "  ANTHROPIC_API_KEY=sk-ant-...\n"
            "  GITHUB_TOKEN=ghp_...\n"
            "  GITHUB_REPO=username/cv-library",
            title="Setup needed", border_style="red"
        ))
        sys.exit(1)

    if not status["accessible"]:
        console.print(f"[red]Cannot access GitHub repo:[/] {status['repo']}")
        console.print("Check your GITHUB_TOKEN has 'repo' scope and the repo name is correct.")
        sys.exit(1)

    console.print(f"[green]✓  Connected to:[/] github.com/{status['repo']}")
    console.print(f"   {status['remote_cv_count']} aligned CVs available\n")

    # Pull everything
    console.print("[cyan]Pulling aligned CVs...[/]")
    aligned_count = sync.pull_all(local_dir="aligned_cvs")

    console.print("[cyan]Pulling base CVs...[/]")
    base_count = sync.pull_base_cvs(local_dir="my_cvs")

    console.print("[cyan]Pulling CV index...[/]")
    sync.pull_index("cv_index.json")

    console.print(Panel(
        f"[bold green]✅  Team setup complete![/]\n\n"
        f"  Aligned CVs pulled:  {aligned_count} new files → [cyan]aligned_cvs/[/]\n"
        f"  Base CVs pulled:     {base_count} new files → [cyan]my_cvs/[/]\n"
        f"  Index updated:       [cyan]cv_index.json[/]\n\n"
        f"You're ready to run:\n"
        f"  [bold cyan]python cv_pilot.py --list[/]       (browse the library)\n"
        f"  [bold cyan]python cv_pilot.py[/]               (align a new CV)\n"
        f"  [bold cyan]python cv_pilot.py --jd job.txt[/]  (JD from file)",
        title="Ready", border_style="green"
    ))

if __name__ == "__main__":
    main()
