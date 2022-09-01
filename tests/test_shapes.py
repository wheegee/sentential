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
    for file in ["Dockerfile", "policy.json", "shapes.py"]:
        assert exists(file)

def test_setup_fixtures():
    copyfile(f"{project}/tests/fixtures/app.py", f"{repo.name}/src/app.py")
    copyfile(f"{project}/tests/fixtures/shapes.py", f"{repo.name}/shapes.py")
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

def test_write():
    result = []
    result.append(runner.invoke(sntl, ["arg", "write", "REQUIRED_ARG", "required_value"]))
    result.append(runner.invoke(sntl, ["arg", "write", "list_arg", f"{['one', 'two', 'three']}"]))
    result.append(runner.invoke(sntl, ["env", "write", "REQUIRED_ENV", "required_value"]))
    result.append(runner.invoke(sntl, ["env", "write", "list_env", f"{['one', 'two', 'three']}"]))
    assert all(result)

def test_local_build():
    result = runner.invoke(sntl, ["build"])
    assert result.exit_code == 0

def test_local_deploy():
    result = runner.invoke(sntl, ["deploy", "local", "--public-url"])
    assert result.exit_code == 0


@flaky(max_runs=10)
def test_local_app():
    results = []
    environment = dict(requests.get("http://localhost:8081/").json())
    for envar in ["REQUIRED_ENV","OPTIONAL_ENV", "list_env"]:
        results.append(envar in environment.keys())
    assert all(results)

def test_local_destroy():
    result = runner.invoke(sntl, ["destroy", "local"])
    assert result.exit_code == 0

def test_delete():
    result = []
    result.append(runner.invoke(sntl, ["arg", "delete", "REQUIRED_ARG", "required_value"]))
    result.append(runner.invoke(sntl, ["arg", "delete", "list_arg", f"{['one', 'two', 'three']}"]))
    result.append(runner.invoke(sntl, ["env", "delete", "REQUIRED_ENV", "required_value"]))
    result.append(runner.invoke(sntl, ["env", "delete", "list_env", f"{['one', 'two', 'three']}"]))
    assert all(result)

