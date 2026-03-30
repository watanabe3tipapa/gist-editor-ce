import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from gist_editor_ce import cli
from gist_editor_ce.github_api import (
    GistApiError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def mock_config():
    return {"token": "test_token_123", "default_public": False, "editor": "vim", "server_port": 0}


class TestAuthCommands:
    def test_auth_login_with_pat(self, cli_runner, mock_config):
        with (
            patch("gist_editor_ce.auth.load_config", return_value=mock_config),
            patch("gist_editor_ce.auth.save_config") as mock_save,
            patch("gist_editor_ce.github_api.get_token_info", return_value={"login": "testuser"}),
        ):
            result = cli_runner.invoke(cli.app, ["auth-login", "--pat", "new_token"])

            assert result.exit_code == 0
            mock_save.assert_called_once()

    def test_auth_status_authenticated(self, cli_runner, mock_config):
        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch(
                "gist_editor_ce.github_api.get_token_info",
                return_value={"login": "testuser", "name": "Test User"},
            ),
        ):
            result = cli_runner.invoke(cli.app, ["auth-status"])

            assert result.exit_code == 0
            assert "testuser" in result.output

    def test_auth_status_not_authenticated(self, cli_runner):
        with (
            patch("gist_editor_ce.auth.get_token", return_value=None),
            patch(
                "gist_editor_ce.github_api.get_token_info",
                side_effect=AuthenticationError("Not authenticated"),
            ),
        ):
            result = cli_runner.invoke(cli.app, ["auth-status"])

            assert result.exit_code == 1

    def test_auth_logout(self, cli_runner, mock_config):
        with (
            patch("gist_editor_ce.auth.load_config", return_value=mock_config),
            patch("gist_editor_ce.auth.save_config") as mock_save,
        ):
            result = cli_runner.invoke(cli.app, ["auth-logout"])

            assert result.exit_code == 0
            assert "Logged out" in result.output


class TestListCommand:
    def test_list_gists(self, cli_runner, mock_config):
        mock_gists = [
            {"id": "abc123", "description": "Test gist", "files": {"test.md": {}}, "public": False},
            {"id": "def456", "description": "", "files": {"a.md": {}, "b.md": {}}, "public": True},
        ]

        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.list_gists", return_value=mock_gists),
        ):
            result = cli_runner.invoke(cli.app, ["list"])

            assert result.exit_code == 0

    def test_list_gists_empty(self, cli_runner, mock_config):
        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.list_gists", return_value=[]),
        ):
            result = cli_runner.invoke(cli.app, ["list"])

            assert result.exit_code == 0
            assert "No gists found" in result.output

    def test_list_gists_error(self, cli_runner):
        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.list_gists", side_effect=GistApiError("API error")),
        ):
            result = cli_runner.invoke(cli.app, ["list"])

            assert result.exit_code == 1


class TestViewCommand:
    def test_view_gist(self, cli_runner, mock_config):
        mock_gist = {
            "id": "abc123",
            "files": {
                "test.md": {"content": "# Hello\n\nWorld"},
            },
        }

        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.get_gist", return_value=mock_gist),
        ):
            result = cli_runner.invoke(cli.app, ["view", "abc123"])

            assert result.exit_code == 0
            assert "Hello" in result.output

    def test_view_gist_specific_file(self, cli_runner, mock_config):
        mock_gist = {
            "id": "abc123",
            "files": {
                "test.md": {"content": "Test content"},
                "other.md": {"content": "Other content"},
            },
        }

        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.get_gist", return_value=mock_gist),
        ):
            result = cli_runner.invoke(cli.app, ["view", "abc123", "--file", "other.md"])

            assert result.exit_code == 0
            assert "Other content" in result.output

    def test_view_gist_file_not_found(self, cli_runner, mock_config):
        mock_gist = {"id": "abc123", "files": {"test.md": {"content": "Test"}}}

        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.get_gist", return_value=mock_gist),
        ):
            result = cli_runner.invoke(cli.app, ["view", "abc123", "--file", "nonexistent.md"])

            assert result.exit_code == 1

    def test_view_gist_all_files(self, cli_runner, mock_config):
        mock_gist = {
            "id": "abc123",
            "files": {
                "test.md": {"content": "Test content"},
                "other.md": {"content": "Other content"},
            },
        }

        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.get_gist", return_value=mock_gist),
        ):
            result = cli_runner.invoke(cli.app, ["view", "abc123", "--all"])

            assert result.exit_code == 0
            assert "Test content" in result.output
            assert "Other content" in result.output


class TestCreateCommand:
    def test_create_gist_abort_empty(self, cli_runner, mock_config):
        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.editor.open_editor", return_value=""),
        ):
            result = cli_runner.invoke(cli.app, ["create"])

            assert result.exit_code == 1
            assert "Aborted" in result.output

    def test_create_gist_success(self, cli_runner, mock_config):
        mock_response = {"html_url": "https://gist.github.com/test/abc123"}

        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.editor.open_editor", return_value="# Test"),
            patch("gist_editor_ce.github_api.create_gist", return_value=mock_response),
        ):
            result = cli_runner.invoke(cli.app, ["create", "--description", "Test"])

            assert result.exit_code == 0
            assert "Created" in result.output


class TestEditCommand:
    def test_edit_gist_no_changes(self, cli_runner, mock_config):
        mock_gist = {"id": "abc123", "files": {"test.md": {"content": "Same content"}}}

        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.get_gist", return_value=mock_gist),
            patch("gist_editor_ce.editor.open_editor", return_value="Same content"),
        ):
            result = cli_runner.invoke(cli.app, ["edit", "abc123"])

            assert result.exit_code == 0
            assert "No changes" in result.output

    def test_edit_gist_with_changes(self, cli_runner, mock_config):
        mock_gist = {"id": "abc123", "files": {"test.md": {"content": "Old content"}}}

        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.get_gist", return_value=mock_gist),
            patch("gist_editor_ce.editor.open_editor", return_value="New content"),
            patch("gist_editor_ce.github_api.update_gist", return_value=mock_gist),
        ):
            result = cli_runner.invoke(cli.app, ["edit", "abc123"])

            assert result.exit_code == 0
            assert "Updated" in result.output


class TestDeleteCommand:
    def test_delete_gist_abort(self, cli_runner):
        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("typer.prompt", return_value="n"),
        ):
            result = cli_runner.invoke(cli.app, ["delete", "abc123"])

            assert result.exit_code == 0
            assert "Aborted" in result.output

    def test_delete_gist_confirm(self, cli_runner):
        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("typer.prompt", return_value="y"),
            patch("gist_editor_ce.github_api.delete_gist", return_value=True),
        ):
            result = cli_runner.invoke(cli.app, ["delete", "abc123"])

            assert result.exit_code == 0
            assert "Deleted" in result.output

    def test_delete_gist_force(self, cli_runner):
        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.delete_gist", return_value=True),
            patch("typer.prompt", return_value="y"),
            patch("gist_editor_ce.cli.typer.prompt", return_value="y"),
        ):
            result = cli_runner.invoke(cli.app, ["delete", "abc123", "--force"])

            assert result.exit_code == 0
            assert "Deleted" in result.output


class TestEmbedCommand:
    def test_embed_gist(self, cli_runner, mock_config):
        mock_gist = {"id": "abc123", "owner": {"login": "testuser"}, "files": {"test.js": {}}}

        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.get_gist", return_value=mock_gist),
        ):
            result = cli_runner.invoke(cli.app, ["embed", "abc123"])

            assert result.exit_code == 0
            assert "gist.github.com" in result.output

    def test_embed_gist_raw(self, cli_runner, mock_config):
        mock_gist = {"id": "abc123", "owner": {"login": "testuser"}, "files": {"test.js": {}}}

        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.get_gist", return_value=mock_gist),
        ):
            result = cli_runner.invoke(cli.app, ["embed", "abc123", "--raw"])

            assert result.exit_code == 0
            assert "https://gist.github.com" in result.output


class TestFilesCommand:
    def test_files_gist(self, cli_runner, mock_config):
        mock_gist = {
            "id": "abc123",
            "files": {
                "test.py": {"language": "Python", "type": "file", "content": "print('hi')"},
                "readme.md": {"language": "Markdown", "type": "file", "content": "# Hello"},
            },
        }

        with (
            patch("gist_editor_ce.auth.get_token", return_value="test_token"),
            patch("gist_editor_ce.github_api.get_gist", return_value=mock_gist),
        ):
            result = cli_runner.invoke(cli.app, ["files", "abc123"])

            assert result.exit_code == 0
            assert "test.py" in result.output
            assert "Python" in result.output


class TestGistApiErrors:
    def test_authentication_error(self):
        from gist_editor_ce.github_api import AuthenticationError

        err = AuthenticationError("Invalid token", 401)
        assert err.status_code == 401
        assert "Invalid token" in str(err)

    def test_not_found_error(self):
        from gist_editor_ce.github_api import NotFoundError

        err = NotFoundError("Gist not found", 404)
        assert err.status_code == 404

    def test_rate_limit_error(self):
        from gist_editor_ce.github_api import RateLimitError

        err = RateLimitError("Rate limit exceeded", 403)
        assert err.status_code == 403


class TestConfig:
    def test_load_config_default(self, tmp_path, monkeypatch):
        from pathlib import Path

        config_dir = tmp_path / "gist-editor-ce"
        config_file = config_dir / "config.toml"

        monkeypatch.setattr("gist_editor_ce.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("gist_editor_ce.config.CONFIG_FILE", config_file)

        from gist_editor_ce.config import load_config, DEFAULT

        result = load_config()
        assert result == DEFAULT

    def test_save_config_creates_directory(self, tmp_path, monkeypatch):
        from pathlib import Path

        config_dir = tmp_path / "gist-editor-ce"
        config_file = config_dir / "config.toml"

        monkeypatch.setattr("gist_editor_ce.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("gist_editor_ce.config.CONFIG_FILE", config_file)

        from gist_editor_ce import config

        config.save_config({"token": "test"})

        assert config_file.exists()


class TestAuth:
    def test_get_token_from_env(self):
        import os

        os.environ["GISTMD_PAT"] = "env_token"

        from gist_editor_ce.auth import get_token

        assert get_token() == "env_token"

        del os.environ["GISTMD_PAT"]

    def test_get_token_none_when_no_config(self, tmp_path, monkeypatch):
        from pathlib import Path
        import importlib
        import os

        config_dir = tmp_path / "gist-editor-ce"
        config_file = config_dir / "config.toml"

        monkeypatch.delenv("GISTMD_PAT", raising=False)
        monkeypatch.setattr("gist_editor_ce.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("gist_editor_ce.config.CONFIG_FILE", config_file)

        import gist_editor_ce.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.get_token() is None
