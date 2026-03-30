import pytest
from gist_editor_ce import __version__


def test_version():
    assert hasattr(__import__("gist_editor_ce"), "__version__")


def test_version_format():
    assert isinstance(__version__, str)
    assert len(__version__.split(".")) >= 2
