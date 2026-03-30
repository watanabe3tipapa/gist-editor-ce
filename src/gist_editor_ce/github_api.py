import requests
from typing import Dict, Any, Optional, List
from .auth import get_token

API_BASE = "https://api.github.com"

GistFile = Dict[str, str]
GistFiles = Dict[str, GistFile]


class GistApiError(Exception):
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(GistApiError):
    pass


class NotFoundError(GistApiError):
    pass


class RateLimitError(GistApiError):
    pass


def _handle_response(response: requests.Response) -> Any:
    if response.status_code == 401:
        raise AuthenticationError("Authentication failed. Check your token.", 401)
    elif response.status_code == 403:
        if "rate limit" in response.text.lower():
            raise RateLimitError("API rate limit exceeded. Try again later.", 403)
        raise AuthenticationError("Access forbidden. Check token permissions.", 403)
    elif response.status_code == 404:
        raise NotFoundError("Resource not found.", 404)
    elif response.status_code >= 400:
        try:
            error_data = response.json()
            message = error_data.get("message", "Unknown error")
        except Exception:
            message = response.text or "Unknown error"
        raise GistApiError(f"API error: {message}", response.status_code)

    response.raise_for_status()
    return response.json() if response.text else None


def _headers() -> Dict[str, str]:
    token = get_token()
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def get_token_info() -> Dict[str, Any]:
    token = get_token()
    if not token:
        raise AuthenticationError(
            "No token configured. Run 'gist-editor-ce auth-login'"
        )

    try:
        r = requests.get(f"{API_BASE}/user", headers=_headers(), timeout=10)
        data = _handle_response(r)
        return data
    except requests.RequestException as e:
        raise GistApiError(f"Network error: {e}")


def list_gists(
    public: Optional[bool] = None,
    page: int = 1,
    per_page: int = 30,
    starred: bool = False,
) -> List[Dict[str, Any]]:
    if starred:
        url = f"{API_BASE}/gists/starred"
    elif public is True:
        url = f"{API_BASE}/gists/public"
    else:
        url = f"{API_BASE}/gists"

    params = {"page": page, "per_page": per_page}

    try:
        r = requests.get(url, headers=_headers(), params=params, timeout=10)
        return _handle_response(r)
    except requests.RequestException as e:
        raise GistApiError(f"Failed to list gists: {e}")


def get_gist(gist_id: str) -> Dict[str, Any]:
    try:
        r = requests.get(f"{API_BASE}/gists/{gist_id}", headers=_headers(), timeout=10)
        return _handle_response(r)
    except requests.RequestException as e:
        raise GistApiError(f"Failed to get gist: {e}")


def create_gist(
    files: GistFiles, description: str = "", public: bool = False
) -> Dict[str, Any]:
    if not files:
        raise GistApiError("At least one file is required")

    for filename, file_data in files.items():
        if not filename:
            raise GistApiError("Filename cannot be empty")
        if "content" not in file_data:
            raise GistApiError(f"File '{filename}' missing 'content' field")

    payload = {"files": files, "description": description, "public": public}

    try:
        r = requests.post(
            f"{API_BASE}/gists", json=payload, headers=_headers(), timeout=10
        )
        return _handle_response(r)
    except requests.RequestException as e:
        raise GistApiError(f"Failed to create gist: {e}")


def update_gist(
    gist_id: str, files: Dict[str, Any], description: Optional[str] = None
) -> Dict[str, Any]:
    if not files:
        raise GistApiError("At least one file update is required")

    payload: Dict[str, Any] = {"files": files}
    if description is not None:
        payload["description"] = description

    try:
        r = requests.patch(
            f"{API_BASE}/gists/{gist_id}", json=payload, headers=_headers(), timeout=10
        )
        return _handle_response(r)
    except requests.RequestException as e:
        raise GistApiError(f"Failed to update gist: {e}")


def delete_gist(gist_id: str) -> bool:
    try:
        r = requests.delete(
            f"{API_BASE}/gists/{gist_id}", headers=_headers(), timeout=10
        )
        _handle_response(r)
        return True
    except requests.RequestException as e:
        raise GistApiError(f"Failed to delete gist: {e}")


def fork_gist(gist_id: str) -> Dict[str, Any]:
    try:
        r = requests.post(
            f"{API_BASE}/gists/{gist_id}/forks", headers=_headers(), timeout=10
        )
        return _handle_response(r)
    except requests.RequestException as e:
        raise GistApiError(f"Failed to fork gist: {e}")


def star_gist(gist_id: str) -> bool:
    try:
        r = requests.put(
            f"{API_BASE}/gists/{gist_id}/star", headers=_headers(), timeout=10
        )
        _handle_response(r)
        return True
    except requests.RequestException as e:
        raise GistApiError(f"Failed to star gist: {e}")


def unstar_gist(gist_id: str) -> bool:
    try:
        r = requests.delete(
            f"{API_BASE}/gists/{gist_id}/star", headers=_headers(), timeout=10
        )
        _handle_response(r)
        return True
    except requests.RequestException as e:
        raise GistApiError(f"Failed to unstar gist: {e}")


def is_starred(gist_id: str) -> bool:
    try:
        r = requests.get(
            f"{API_BASE}/gists/{gist_id}/star", headers=_headers(), timeout=10
        )
        return r.status_code == 204
    except requests.RequestException:
        return False


def get_gist_files(gist_id: str) -> List[str]:
    gist = get_gist(gist_id)
    return list(gist.get("files", {}).keys())


def add_file_to_gist(gist_id: str, filename: str, content: str) -> Dict[str, Any]:
    return update_gist(gist_id, files={filename: {"content": content}})


def delete_file_from_gist(gist_id: str, filename: str) -> Dict[str, Any]:
    return update_gist(gist_id, files={filename: None})
