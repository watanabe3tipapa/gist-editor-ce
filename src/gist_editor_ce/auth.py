import os
import webbrowser
import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from .config import load_config, save_config

OAUTH_CLIENT_ID = "Iv1.placeholder"
OAUTH_SCOPES = "gist"
CALLBACK_PORT = 8765


def get_token() -> str:
    tok = os.getenv("GISTMD_PAT")
    if tok:
        return tok
    cfg = load_config()
    return cfg.get("token")


def set_token(token: str):
    cfg = load_config()
    cfg["token"] = token
    cfg["auth_method"] = "pat"
    save_config(cfg)


def clear_token():
    cfg = load_config()
    cfg.pop("token", None)
    cfg.pop("auth_method", None)
    save_config(cfg)


def get_auth_method() -> str:
    cfg = load_config()
    return cfg.get("auth_method", "pat")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/callback":
            params = parse_qs(parsed.query)
            OAuthCallbackHandler.auth_code = params.get("code", [None])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authentication successful!</h1><p>You can close this window.</p></body></html>"
            )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def exchange_code_for_token(code: str) -> str:
    token_url = "https://github.com/login/oauth/access_token"
    data = {
        "client_id": OAUTH_CLIENT_ID,
        "code": code,
    }
    headers = {"Accept": "application/json"}

    try:
        r = requests.post(token_url, json=data, headers=headers, timeout=10)
        r.raise_for_status()
        result = r.json()

        if "error" in result:
            raise Exception(result.get("error_description", result.get("error")))

        return result.get("access_token", "")
    except Exception as e:
        raise Exception(f"Failed to exchange code for token: {e}")


def oauth_login() -> str:
    print("Starting OAuth flow...")
    print("Note: For full OAuth support, you need to register an OAuth App on GitHub.")
    print("For now, using PAT authentication is recommended.")
    print()
    print("To use OAuth in production:")
    print("1. Go to GitHub Settings > Developer settings > OAuth Apps")
    print("2. Create a new OAuth App")
    print("3. Set callback URL to: http://localhost:8765/callback")
    print("4. Update OAUTH_CLIENT_ID in auth.py")
    print()

    authorize_url = (
        f"https://github.com/login/oauth/authorize?client_id={OAUTH_CLIENT_ID}&scope={OAUTH_SCOPES}"
    )

    print("Opening browser for authorization...")
    webbrowser.open(authorize_url)

    server = HTTPServer(("localhost", CALLBACK_PORT), OAuthCallbackHandler)

    def wait_for_callback():
        server.handle_request()

    thread = threading.Thread(target=wait_for_callback, daemon=True)
    thread.start()

    print(f"Waiting for callback on http://localhost:{CALLBACK_PORT}...")
    print("Complete the authorization in your browser.")

    start_time = time.time()
    while OAuthCallbackHandler.auth_code is None:
        if time.time() - start_time > 300:
            server.shutdown()
            raise Exception("OAuth timeout. Please try again.")
        time.sleep(0.5)

    server.shutdown()

    code = OAuthCallbackHandler.auth_code
    OAuthCallbackHandler.auth_code = None

    print("Authorization received. Exchanging for token...")
    token = exchange_code_for_token(code)

    if not token:
        raise Exception("Failed to get access token")

    print("OAuth authentication successful!")
    return token


def is_authenticated() -> bool:
    from . import github_api

    try:
        github_api.get_token_info()
        return True
    except Exception:
        return False


def get_current_user():
    from . import github_api

    return github_api.get_token_info()
