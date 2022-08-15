import in_place
from os.path import exists
from tests.helper import *
from shutil import copyfile
from sentential.sntl import root as sntl
from flaky import flaky
import requests


def test_init():
    result = runner.invoke(sntl, ["init", "test", "python"])
    assert result.exit_code == 0


def test_files_exist():
    for file in [
        "Dockerfile",
        "policy.json",
    ]:
        assert exists(file)


def test_env_write():
    result = runner.invoke(sntl, ["env", "write", "envvar", "test"])
    assert result.exit_code == 0


def test_local_deploy():
    copyfile(f"{project}/tests/fixtures/app.py", f"{repo.name}/src/app.py")
    copyfile(
        f"{project}/tests/fixtures/requirements.txt",
        f"{repo.name}/src/requirements.txt",
    )
    with in_place.InPlace(f"{repo.name}/Dockerfile") as fp:
        for line in fp:
            if "# insert application specific build steps here" in line:
                fp.write("RUN pip install -r requirements.txt\n")
            else:
                fp.write(line)

    result = runner.invoke(sntl, ["local", "deploy", "--public-url"])
    assert result.exit_code == 0


@flaky(max_runs=10)
def test_local_app():
    assert requests.get("http://localhost:8081/envvar").json() == {"ENVVAR": "test"}


def test_local_destroy():
    result = runner.invoke(sntl, ["local", "destroy"])
    assert result.exit_code == 0


def test_env_delete():
    result = runner.invoke(sntl, ["env", "delete", "envvar"])
    assert result.exit_code == 0
