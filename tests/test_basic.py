import in_place
from os.path import exists
from tests.helper import EphemeralProject
from shutil import copyfile
from sentential.sntl import root as sntl
from flaky import flaky
import requests


class TestCase(EphemeralProject):
    def test_init(self):
        result = self.runner.invoke(sntl, ["init", "test", "python"])
        assert result.exit_code == 0

    def test_files_exist(self):
        for file in ["Dockerfile", "policy.json", "shapes.py"]:
            assert exists(file)

    def test_setup_fixtures(self):
        copyfile(
            f"{self.project}/tests/fixtures/app.py", f"{self.repo.name}/src/app.py"
        )
        copyfile(
            f"{self.project}/tests/fixtures/requirements.txt",
            f"{self.repo.name}/src/requirements.txt",
        )
        with in_place.InPlace(f"{self.repo.name}/Dockerfile") as fp:
            for line in fp:
                if "# insert application specific build steps here" in line:
                    fp.write("RUN pip install -r requirements.txt\n")
                else:
                    fp.write(line)

    def test_env_write(self):
        result = self.runner.invoke(sntl, ["env", "write", "key", "value"])
        assert result.exit_code == 0

    def test_local_build(self):
        result = self.runner.invoke(sntl, ["build"])
        assert result.exit_code == 0

    def test_local_deploy(self):
        result = self.runner.invoke(sntl, ["deploy", "local", "--public-url"])
        assert result.exit_code == 0

    @flaky(max_runs=10)
    def test_local_lambda(self):
        results = []
        environment = dict(requests.get("http://localhost:8081/").json())
        for envar in ["key"]:
            results.append(envar in environment.keys())
        assert all(results)

    def test_local_destroy(self):
        result = self.runner.invoke(sntl, ["destroy", "local"])
        assert result.exit_code == 0

    def test_env_delete(self):
        result = self.runner.invoke(sntl, ["env", "delete", "key"])
        assert result.exit_code == 0
