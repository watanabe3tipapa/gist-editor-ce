import typer
import os
from typing import List
from rich.console import Console
from rich.table import Table
from . import github_api, editor, auth, server
from .github_api import GistApiError, AuthenticationError, NotFoundError, RateLimitError

app = typer.Typer(help="gist-editor-ce — CLI+GUI Gist Markdown editor")
console = Console()


def handle_api_error(e: Exception):
    if isinstance(e, AuthenticationError):
        console.print(f"[red]Authentication error:[/red] {e.message}")
        console.print("[yellow]Run 'gist-editor-ce auth-login' to authenticate[/yellow]")
    elif isinstance(e, NotFoundError):
        console.print(f"[red]Not found:[/red] {e.message}")
    elif isinstance(e, RateLimitError):
        console.print(f"[red]Rate limit exceeded:[/red] {e.message}")
        console.print("[yellow]Try again in a few minutes[/yellow]")
    elif isinstance(e, GistApiError):
        console.print(f"[red]API error:[/red] {e.message}")
    else:
        console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(code=1)


@app.command()
def auth_login(
    pat: str = typer.Option(None, help="Personal access token to use"),
    oauth: bool = typer.Option(False, "--oauth", help="Use OAuth authentication"),
    save: bool = typer.Option(True, help="Save token to config"),
):
    if oauth:
        try:
            token = auth.oauth_login()
        except Exception as e:
            console.print(f"[red]OAuth failed:[/red] {e}")
            raise typer.Exit(code=1)
    elif not pat:
        pat = typer.prompt("Enter Personal Access Token (with gist scope)", hide_input=True)

    token = pat if pat else token

    if save:
        auth.set_token(token)
        console.print("[green]Token saved to config[/green]")
    else:
        os.environ["GISTMD_PAT"] = token
        console.print("[yellow]Token set for session only (export GISTMD_PAT to persist)[/yellow]")

    try:
        user = github_api.get_token_info()
        console.print(f"[green]Authenticated as:[/green] {user.get('login', 'unknown')}")
    except GistApiError as e:
        console.print(f"[yellow]Token saved but verification failed: {e}[/yellow]")


@app.command()
def auth_status():
    try:
        user = github_api.get_token_info()
        console.print(f"[green]Authenticated as:[/green] {user.get('login')}")
        console.print(f"Name: {user.get('name', 'N/A')}")
    except GistApiError as e:
        handle_api_error(e)


@app.command()
def auth_logout():
    auth.clear_token()
    console.print("[green]Logged out[/green]")


@app.command()
def list(
    public: bool = typer.Option(False, "--public", help="List public gists"),
    starred: bool = typer.Option(False, "--starred", help="List starred gists"),
    page: int = typer.Option(1, help="Page number"),
):
    try:
        gists = github_api.list_gists(public=public if public else None, page=page, starred=starred)

        if not gists:
            console.print("[yellow]No gists found[/yellow]")
            return

        table = Table(title="Your Gists")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Files", style="green")
        table.add_column("Public", style="magenta")

        for item in gists:
            files = item.get("files", {})
            file_count = len(files)
            is_public = "Yes" if item.get("public") else "No"
            desc = item.get("description") or "(no description)"
            table.add_row(item["id"][:12] + "...", desc[:50], str(file_count), is_public)

        console.print(table)
        console.print(f"\n[dim]Page {page} - Total shown: {len(gists)}[/dim]")

    except GistApiError as e:
        handle_api_error(e)


@app.command()
def view(
    gist_id: str,
    file: str = typer.Option(None, "--file", "-f", help="Specific file to view"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all files"),
):
    try:
        g = github_api.get_gist(gist_id)
        files = g.get("files", {})

        if not files:
            console.print("[yellow]No files in this gist[/yellow]")
            return

        if all:
            for fname, fdata in files.items():
                console.print(f"\n[bold cyan]=== {fname} ===[/bold cyan]")
                console.print(fdata.get("content", ""))
        else:
            name = file or next(iter(files))
            if name not in files:
                console.print(f"[red]File '{name}' not found[/red]")
                console.print(f"Available files: {', '.join(files.keys())}")
                raise typer.Exit(code=1)
            console.print(files[name].get("content", ""))

    except GistApiError as e:
        handle_api_error(e)


@app.command()
def create(
    description: str = typer.Option("", "--description", "-d", help="Gist description"),
    public: bool = typer.Option(False, "--public", "-p", help="Make public"),
    filename: str = typer.Option(
        "gist.md", "--filename", "-f", help="Filename (use multiple for multi-file)"
    ),
    files: List[str] = typer.Option(None, "--file", help="Additional files to add"),
):
    contents = []

    if files:
        for fpath in files:
            if not os.path.exists(fpath):
                console.print(f"[red]File not found:[/red] {fpath}")
                raise typer.Exit(code=1)
            with open(fpath, "r", encoding="utf-8") as f:
                fname = os.path.basename(fpath)
                contents.append((fname, f.read()))

    if not contents:
        content = editor.open_editor("# New Gist\n")
        if not content.strip():
            console.print("[yellow]Aborted: empty content[/yellow]")
            raise typer.Exit(code=1)
        contents = [(filename, content)]

    gist_files = {name: {"content": content} for name, content in contents}

    try:
        res = github_api.create_gist(files=gist_files, description=description, public=public)
        console.print(f"[green]Created:[/green] {res['html_url']}")
    except GistApiError as e:
        handle_api_error(e)


@app.command()
def edit(
    gist_id: str,
    file: str = typer.Option(None, "--file", "-f", help="Specific file to edit"),
    all_files: bool = typer.Option(False, "--all", "-a", help="Edit all files sequentially"),
):
    try:
        g = github_api.get_gist(gist_id)
        files = g.get("files", {})

        if not files:
            console.print("[yellow]No files in this gist[/yellow]")
            return

        if all_files:
            for fname, fdata in files.items():
                content = fdata.get("content", "")
                new_content = editor.open_editor(content)
                if new_content.strip() != content.strip():
                    github_api.update_gist(gist_id, files={fname: {"content": new_content}})
                    console.print(f"[green]Updated:[/green] {fname}")
                else:
                    console.print(f"[dim]No changes:[/dim] {fname}")
        else:
            name = file or next(iter(files))
            if name not in files:
                console.print(f"[red]File '{name}' not found[/red]")
                raise typer.Exit(code=1)

            content = files[name].get("content", "")
            new_content = editor.open_editor(content)

            if new_content.strip() == content.strip():
                console.print("[yellow]No changes[/yellow]")
                raise typer.Exit()

            github_api.update_gist(gist_id, files={name: {"content": new_content}})
            console.print(f"[green]Updated:[/green] {name}")

    except GistApiError as e:
        handle_api_error(e)


@app.command()
def add(
    gist_id: str,
    filename: str = typer.Option(..., "--filename", "-f", help="Filename for new file"),
    content: str = typer.Option(
        None, "--content", "-c", help="File content (opens editor if not provided)"
    ),
    from_file: str = typer.Option(None, "--from-file", help="Read content from file"),
):
    if from_file:
        if not os.path.exists(from_file):
            console.print(f"[red]File not found:[/red] {from_file}")
            raise typer.Exit(code=1)
        with open(from_file, "r", encoding="utf-8") as f:
            file_content = f.read()
    elif content:
        file_content = content
    else:
        file_content = editor.open_editor("")
        if not file_content.strip():
            console.print("[yellow]Aborted: empty content[/yellow]")
            raise typer.Exit(code=1)

    try:
        github_api.add_file_to_gist(gist_id, filename, file_content)
        console.print(f"[green]Added file:[/green] {filename}")
    except GistApiError as e:
        handle_api_error(e)


@app.command()
def delete(
    gist_id: str,
    file: str = typer.Option(None, "--file", "-f", help="Delete specific file (not the gist)"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    try:
        if file:
            if force:
                confirm = "y"
            else:
                confirm = typer.prompt(
                    f"Delete file '{file}' from gist {gist_id}? [y/N]", default="n"
                )
            if str(confirm).lower() != "y":
                console.print("[yellow]Aborted[/yellow]")
                return

            g = github_api.get_gist(gist_id)
            files = g.get("files", {})
            if len(files) <= 1:
                console.print(
                    "[red]Cannot delete the only file in a gist. Delete the entire gist instead.[/red]"
                )
                raise typer.Exit(code=1)

            github_api.delete_file_from_gist(gist_id, file)
            console.print(f"[green]Deleted file:[/green] {file}")
        else:
            if force:
                confirm = "y"
            else:
                confirm = typer.prompt(
                    f"Delete gist {gist_id}? This cannot be undone. [y/N]", default="n"
                )
            if str(confirm).lower() != "y":
                console.print("[yellow]Aborted[/yellow]")
                return

            github_api.delete_gist(gist_id)
            console.print("[green]Deleted[/green]")

    except GistApiError as e:
        handle_api_error(e)


@app.command()
def fork(gist_id: str):
    try:
        res = github_api.fork_gist(gist_id)
        console.print(f"[green]Forked:[/green] {res['html_url']}")
    except GistApiError as e:
        handle_api_error(e)


@app.command()
def star(gist_id: str):
    try:
        github_api.star_gist(gist_id)
        console.print(f"[green]Starred:[/green] {gist_id}")
    except GistApiError as e:
        handle_api_error(e)


@app.command()
def unstar(gist_id: str):
    try:
        github_api.unstar_gist(gist_id)
        console.print(f"[yellow]Unstarred:[/yellow] {gist_id}")
    except GistApiError as e:
        handle_api_error(e)


@app.command()
def serve(
    gist_id: str,
    port: int = typer.Option(0, "--port", "-p", help="Port (0 = auto)"),
):
    try:
        g = github_api.get_gist(gist_id)
        files = g.get("files", {})

        if not files:
            console.print("[yellow]No files in this gist[/yellow]")
            raise typer.Exit(code=1)

        console.print(f"[green]Files in gist:[/green] {', '.join(files.keys())}")

        url = server.serve(gist_id, port=port)
        console.print(f"Serving at {url}")
        console.print("Press Ctrl+C to stop")

    except GistApiError as e:
        handle_api_error(e)


@app.command()
def embed(
    gist_id: str,
    file: str = typer.Option(None, "--file", "-f", help="Specific file"),
    raw: bool = typer.Option(False, "--raw", help="Output raw URL instead of script tag"),
):
    try:
        g = github_api.get_gist(gist_id)
        files = g.get("files", {})
        owner = g.get("owner", {}).get("login", "<username>")

        name = file or next(iter(files))

        if raw:
            url = f"https://gist.github.com/{owner}/{gist_id}#{name}"
        else:
            url = (
                f'<script src="https://gist.github.com/{owner}/{gist_id}.js?file={name}"></script>'
            )

        console.print(url)

    except GistApiError as e:
        handle_api_error(e)


@app.command()
def files(gist_id: str):
    try:
        g = github_api.get_gist(gist_id)
        files = g.get("files", {})

        if not files:
            console.print("[yellow]No files in this gist[/yellow]")
            return

        table = Table(title=f"Files in {gist_id}")
        table.add_column("Filename", style="cyan")
        table.add_column("Language", style="green")
        table.add_column("Size", style="yellow")
        table.add_column("Type", style="magenta")

        for fname, fdata in files.items():
            size = len(fdata.get("content", ""))
            language = fdata.get("language", "text")
            ftype = fdata.get("type", "file")
            table.add_row(fname, language or "N/A", f"{size} bytes", ftype)

        console.print(table)

    except GistApiError as e:
        handle_api_error(e)


if __name__ == "__main__":
    app()
