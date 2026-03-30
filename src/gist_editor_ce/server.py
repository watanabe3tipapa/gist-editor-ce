from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown
import webbrowser
import threading
import uvicorn
from .github_api import get_gist, update_gist
from .config import load_config
from pathlib import Path

HERE = Path(__file__).parent
templates = Environment(
    loader=FileSystemLoader(str(HERE / "templates")),
    autoescape=select_autoescape(["html", "xml"]),
)

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")


@app.get("/edit/{gist_id}", response_class=HTMLResponse)
def edit_page(gist_id: str):
    gist = get_gist(gist_id)
    files = gist.get("files", {})
    if not files:
        return PlainTextResponse("No files in gist", status_code=404)

    owner = gist.get("owner", {}).get("login", "")
    first_name = next(iter(files))
    content = files[first_name].get("content", "")
    rendered = markdown.markdown(content)
    gist_url = f"https://gist.github.com/{owner}/{gist_id}" if owner else None

    html = templates.get_template("edit.html").render(
        gist_id=gist_id,
        filename=first_name,
        content=content,
        rendered=rendered,
        owner=owner,
        gist_url=gist_url,
    )
    return HTMLResponse(html)


@app.post("/save/{gist_id}")
def save(
    gist_id: str,
    filename: str = Form(...),
    content: str = Form(...),
    description: str = Form(None),
):
    files = {filename: {"content": content}}
    update_gist(gist_id, files=files, description=description)
    return RedirectResponse(f"/edit/{gist_id}", status_code=303)


@app.post("/__render")
async def render_md(request: Request):
    text = await request.body()
    html = markdown.markdown(text.decode("utf-8"))
    return HTMLResponse(html)


def serve(gist_id: str, port: int = 0):
    cfg = load_config()
    port = port or cfg.get("server_port") or 0
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{config.port}/edit/{gist_id}"
    webbrowser.open(url)
    return url
