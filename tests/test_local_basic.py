import pytest
import requests
import in_place
from flaky import flaky
from os.path import exists
from shutil import copyfile

def test_init(invoke):
    result = invoke(["init", "test", "python"])
    assert result.exit_code == 0

def test_files_exist():
    for file in ["Dockerfile", "policy.json", "shapes.py"]:
        assert exists(file)

def test_setup_fixtures(repo, project):
    copyfile(
            f"{project}/tests/fixtures/app.py", f"{repo.name}/src/app.py"
        )
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

def test_env_write(invoke):
    result = invoke(["env", "write", "key", "value"])
    assert result.exit_code == 0

def test_local_build(invoke):
    result = invoke(["build"])
    assert result.exit_code == 0

def test_local_deploy(invoke):
    result = invoke(["deploy", "local", "--public-url"])
    pytest.deployment_url = result.output
    assert result.exit_code == 0

@flaky(max_runs=10)
def test_local_lambda():
    results = []
    environment = dict(requests.get(pytest.deployment_url).json())
    for envar in ["key"]:
        results.append(envar in environment.keys())
    assert all(results)

def test_local_destroy(invoke):
    result = invoke(["destroy", "local"])
    assert result.exit_code == 0

def test_arg_delete(invoke):
    result = invoke(["arg", "clear"])
    assert result.exit_code == 0

def test_env_delete(invoke):
    result = invoke(["env", "clear"])
    assert result.exit_code == 0

def test_config_delete(invoke):
    result = invoke(["config", "clear"])
    assert result.exit_code == 0
