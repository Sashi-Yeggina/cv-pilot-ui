#!/usr/bin/env python3
"""
upload_base_cvs.py — Push your 8+ base CVs to GitHub (run once)
---------------------------------------------------------------
Run this once to upload all your source CVs to the shared repo.
After this, any team member who runs team_pull.py gets them automatically.

Usage:
  python upload_base_cvs.py                    # uploads everything in ./my_cvs/
  python upload_base_cvs.py --folder ./my_cvs  # explicit folder
"""

import sys, argparse
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import track
except ImportError:
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Upload base CVs to GitHub")
    parser.add_argument("--folder", default="./my_cvs", help="Folder containing your base CVs")
    args = parser.parse_args()

    from cv_sync import CVSync
    sync = CVSync(script_dir=str(Path(__file__).parent))

    status = sync.status()
    if not status["enabled"]:
        console.print("[red]GitHub sync not configured. See .env.example[/]")
        sys.exit(1)

    folder = Path(args.folder)
    if not folder.exists():
        console.print(f"[red]Folder not found:[/] {folder}")
        sys.exit(1)

    docx_files = list(folder.glob("*.docx")) + list(folder.glob("*.DOCX"))
    if not docx_files:
        console.print(f"[yellow]No DOCX files found in {folder}[/]")
        sys.exit(0)

    console.print(Panel(
        f"[bold cyan]Uploading {len(docx_files)} base CVs to GitHub[/]\n"
        f"Repo: [cyan]{status['repo']}[/]\n"
        f"Folder: [cyan]{folder}[/]",
        border_style="cyan"
    ))

    success = 0
    for f in track(docx_files, description="Uploading..."):
        if sync.push_base_cv(str(f)):
            success += 1

    console.print(f"\n[green]✓  {success}/{len(docx_files)} CVs uploaded to GitHub.[/]")
    console.print(f"[dim]Your sales team can now run [cyan]python team_pull.py[/dim] to get them.[/]")


if __name__ == "__main__":
    main()
