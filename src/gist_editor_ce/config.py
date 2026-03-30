import os
from pathlib import Path
import toml

CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "gist-editor-ce"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT = {
    "token": None,
    "default_public": False,
    "editor": os.getenv("EDITOR", "nano"),
    "server_port": 0,
}


def load_config():
    if CONFIG_FILE.exists():
        return toml.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return DEFAULT.copy()


def save_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    CONFIG_FILE.write_text(toml.dumps(cfg), encoding="utf-8")
    os.chmod(CONFIG_FILE, 0o600)
