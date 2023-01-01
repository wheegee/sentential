from shutil import copyfile
from time import sleep
import pytest
from tests.helpers import rewrite
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.mounts.local_lambda_public_url import LocalLambdaPublicUrlMount
from sentential.lib.shapes import Image
from sentential.lib.clients import clients
import requests


@pytest.fixture(scope="class")
def http_handler_returns_environ(init):
    copyfile("./fixtures/app_http.py", f"{init}/src/app.py")
    copyfile("./fixtures/requirements_http.txt", f"{init}/src/requirements.txt")
    rewrite(
        "./Dockerfile",
        "# insert application specific build steps here",
        "RUN pip install -r requirements.txt",
    )


@pytest.mark.usefixtures("moto", "init", "http_handler_returns_environ", "cwi")
class TestAwsLambdaPublicUrlMount:
    def test_deploy(self, cwi: Image, local_lambda_driver: LocalLambdaDriver):
        ontology = local_lambda_driver.ontology
        ontology.envs.write("HELLO", ["THIS_IS_ENV"])
        image = local_lambda_driver.deploy(
            cwi, {"AWS_ENDPOINT": "http://host.docker.internal:5000"}
        )
        LocalLambdaPublicUrlMount(ontology).mount()
        assert image == cwi

    def test_containers(self):
        assert any(container.name == "sentential" for container in clients.docker.container.list())
        assert any(container.name == "sentential-gw" for container in clients.docker.container.list())

    def test_invoke(self):
        sleep(5)
        resp = requests.get("http://localhost:8999")
        assert resp.status_code == 200
        assert "HELLO" in resp.json()
