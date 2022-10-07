from time import sleep
import pytest
import requests
import in_place
from os.path import exists
from shutil import copyfile
from tests.helpers import retry

def test_init(invoke):
    result = invoke(["init", "test", "python"])
    assert result.exit_code == 0


def test_files_exist():
    for file in ["Dockerfile", "policy.json", "shapes.py"]:
        assert exists(file)


def test_setup_fixtures(repo, project):
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


def test_write(invoke):
    result = invoke(["envs", "write", "key", "value"])
    assert result.exit_code == 0


def test_aws_build(invoke):
    result = invoke(["build"])
    assert result.exit_code == 0

def test_aws_login_ecr(invoke):
    result = invoke(['login'])
    assert result.exit_code == 0

def test_aws_publish(invoke):
    result = invoke(["publish"])
    assert result.exit_code == 0


def test_aws_deploy(invoke):
    result = invoke(["deploy", "aws", "latest", "--public-url"])
    pytest.deployment_url = result.output  # type: ignore
    assert result.exit_code == 0


@retry(30)
def test_aws_lambda_health():
    sleep(1)
    assert requests.get(pytest.deployment_url).status_code == 200  # type: ignore


@retry(30)
def test_aws_lambda():
    results = []
    environment = dict(requests.get(pytest.deployment_url).json())  # type: ignore
    for envar in ["key"]:
        results.append(envar in environment.keys())
    assert all(results)


def test_aws_destroy(invoke):
    result = invoke(["destroy", "aws"])
    assert result.exit_code == 0


def test_args_delete(invoke):
    result = invoke(["args", "clear"])
    assert result.exit_code == 0


def test_envs_delete(invoke):
    result = invoke(["envs", "clear"])
    assert result.exit_code == 0


def test_configs_delete(invoke):
    result = invoke(["configs", "clear"])
    assert result.exit_code == 0
