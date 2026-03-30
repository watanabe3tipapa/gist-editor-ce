import os
import subprocess
from tempfile import NamedTemporaryFile


def open_editor(initial_text: str = "", editor_cmd: str = None) -> str:
    editor = editor_cmd or os.getenv("EDITOR", "vim")
    with NamedTemporaryFile(
        suffix=".md", delete=False, mode="w+", encoding="utf-8"
    ) as tf:
        tf.write(initial_text)
        tf.flush()
        path = tf.name
    cmd = editor.split() + [path]
    subprocess.run(cmd)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        os.unlink(path)
    except Exception:
        pass
    return content
