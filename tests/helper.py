import pytest
import tempfile
from os import getcwd
from typer.testing import CliRunner
from IPython import embed

class EphemeralProject:
    repo = tempfile.TemporaryDirectory()
    runner = CliRunner()
    project = getcwd()
    
    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()
        cls.repo = tempfile.TemporaryDirectory()

    def setUp(self):
        self.repo = self.__class__.repo
        self.runner = self.__class__.runner
        self.project = self.__class__.project

    @pytest.fixture(autouse=True)
    def run_in_tmp_dir(self, monkeypatch):
        monkeypatch.chdir(self.repo.name)
        yield
        monkeypatch.chdir(self.project)


