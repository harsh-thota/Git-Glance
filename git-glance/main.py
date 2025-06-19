import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.text import Text
from config import add_repo, remove_repo, load_config
from git import get_repo_status, is_git_repo, fetch_repo


app = typer.Typer()
console = Console()

def display_status_table(statuses: list[dict]):
    table = Table(title="[bold]Git Repositories Status[/bold]", show_lines=True, show_edge=True, row_styles=["", ""], expand=True)

    table.add_column("Alias", style="cyan", no_wrap=True)
    table.add_column("Path", style="dim")
    table.add_column("Branch", style="green")
    table.add_column("Uncommitted Changes", justify="right")
    table.add_column("Unpushed", justify="right")
    table.add_column("Needs Pull", justify="center")

    for s in statuses:
        uncomitted_style = "green" if s.get("uncomitted", 0) == 0 else "yellow"
        unpushed_style = "green" if s.get("unpushed", 0) == 0 else "red"
        needs_pull_style = "green" if not s.get("needs_pull", False) else "red"

        if "error" in s:
            alias = Text(s.get("alias", "<unknown>"), style="red")
            path = Text(s["path"], style="red")
            branch = Text("ERROR", style="red")
            uncommitted = unpushed = needs_pull = Text("ERROR", style="red")
        else:
            alias = s.get("alias", "<no-alias>")
            path = str(s["path"])
            branch = s["branch"]
            uncommitted = Text(str(s["uncomitted"]), style=uncomitted_style)
            unpushed = Text(str(s["unpushed"]), style=unpushed_style)
            needs_pull = Text("Yes" if s["needs_pull"] else "No", style=needs_pull_style)

        table.add_row(alias, path, branch, uncommitted, unpushed, needs_pull)

    console.print(table)

@app.command()
def list():
    """List all tracked repositories."""
    config = load_config()
    if not config["repos"]:
        print("[yellow]No repositories being tracked.[/yellow]")
        raise typer.Exit()

    table = Table(title="Tracked Git Repositories", expand=True, show_lines=True)
    table.add_column("Alias", style="cyan")
    table.add_column("Path", style="dim")

    for repo in config["repos"]:
        table.add_row(repo["alias"], repo["path"])

    console.print(table)


@app.command()
def fetch():
    """Fetch updates for all tracked git repositories."""
    config = load_config()
    repos = config.get("repos", [])
    if not repos:
        console.print("[yellow]No repositories are being tracked.[/yellow]")
        raise typer.Exit()

    console.print("[bold cyan]Fetching updates for all repos...[/bold cyan]")
    for repo in repos:
        try:
            fetch_repo(repo["path"])
            console.print(f"[green]✓ {repo['alias']}[/green] fetched successfully.")
        except ValueError as e:
            console.print(f"[red]✗ {repo['alias']}[/red] fetch failed: {e}")


@app.command()
def status():
    """Show status of all tracked git repositories"""
    config = load_config()
    statuses = []

    for repo in config["repos"]:
        stat = get_repo_status(repo["path"])
        stat["alias"] = repo.get("alias", "<no-alias>")
        statuses.append(stat)

    display_status_table(statuses)

@app.command()
def add(path: str, alias: str = typer.Option(..., help="Enter a nickname for the repo.")):
    """Add a new git repo to the tracking list."""
    try:
        if not Path(path).expanduser().resolve().exists():
            console.print(f"[bold red]Error: The path '{path}' does not exist.[/bold red]")
            raise typer.Exit(1)
        
        if not is_git_repo(path):
            console.print(f"[bold red]Error: The path '{path}' is not a valid Git repository.[/bold red]")
            raise typer.Exit(1)
        add_repo(path, alias)
        console.print(f"[bold green]Added {path} to the tracking list.[/bold green]")
    except ValueError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

@app.command()
def remove(
    path: str = typer.Option(None, help="Path to the git repo to remove."),
    alias: str = typer.Option(None, help="Alias of the repo to remove (optional).")
):
    """Remove a git repo from the tracking list."""
    if not path and not alias:
        console.print("[bold red]Error: Either a path or an alias must be provided.[/bold red]")
        raise typer.Exit(1)
    try:
        remove_repo(path, alias)
        console.print(f"[bold green]Removed repo with path '{path}' or alias '{alias}' from the tracking list.[/bold green]")
    except ValueError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

if __name__ == "__main__":
    app()