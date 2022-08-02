import pytest
from typer.testing import CliRunner
import tempfile
from os import getcwd

runner = CliRunner()
home = getcwd()
repo_dir = tempfile.TemporaryDirectory()

def teardown_module(module):
    repo_dir.cleanup()

@pytest.fixture(autouse=True)
def chdir(monkeypatch):
    monkeypatch.chdir(repo_dir.name)
    yield
    monkeypatch.chdir(home)