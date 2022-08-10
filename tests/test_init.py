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

def test_config_write():
    result = runner.invoke(sntl, ["config", "write", "config", "hello"])
    assert result.exit_code == 0

def test_secret_write():
    result = runner.invoke(sntl, ["secret", "write", "secret", "hello"])
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

    result = runner.invoke(sntl, ["local", "deploy"])
    assert result.exit_code == 0

@flaky(max_runs=10)
def test_local_app():
    assert requests.get("http://localhost:8081/secret").json() == { "SECRET": "hello" }
    assert requests.get("http://localhost:8081/config").json() == { "CONFIG": "hello" }
    

def test_local_destroy():
    result = runner.invoke(sntl, ["local", "destroy"])
    assert result.exit_code == 0

def test_config_delete():
    result = runner.invoke(sntl, ["config", "delete", "config"])
    assert result.exit_code == 0

def test_secret_delete():
    result = runner.invoke(sntl, ["secret", "delete", "secret"])
    assert result.exit_code == 0
