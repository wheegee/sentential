import pytest
import requests
import backoff
from shutil import copyfile
from python_on_whales.components.image.cli_wrapper import Image
from sentential.lib.shapes import Architecture
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.mounts.local_lambda_public_url import LocalLambdaPublicUrlMount
from sentential.lib.clients import clients
from tests.helpers import rewrite


@pytest.fixture(scope="class")
def http_handler_returns_environ(init):
    copyfile("./fixtures/app_http.py", f"{init}/src/app.py")
    copyfile("./fixtures/requirements_http.txt", f"{init}/src/requirements.txt")
    rewrite(
        "./Dockerfile",
        "# insert application specific build steps here",
        "ARG buildarg\nENV BUILDARG=$buildarg\nRUN pip install -r requirements.txt",
    )


@pytest.mark.usefixtures("moto", "init", "http_handler_returns_environ")
class TestAwsLambdaPublicUrlMount:
    def test_build(self, local_images_driver: LocalImagesDriver):
        local_images_driver.ontology.args.write("buildarg", ["present"])
        local_images_driver.build(Architecture.system())

    def test_deploy(self, cwi: Image, local_lambda_driver: LocalLambdaDriver):
        local_lambda_driver.ontology.envs.write("ENVVAR", ["present"])
        message = local_lambda_driver.deploy(
            cwi, {"AWS_ENDPOINT": "http://host.docker.internal:5000"}
        )
        LocalLambdaPublicUrlMount(local_lambda_driver.ontology).mount()
        assert "AKIAIOSFODNN7EXAMPLE-test" in message

    def test_containers(self):
        assert any(
            container.name == "sentential"
            for container in clients.docker.container.list()
        )
        assert any(
            container.name == "sentential-gw"
            for container in clients.docker.container.list()
        )

    @backoff.on_exception(backoff.expo, requests.exceptions.ConnectionError, max_time=5)
    def test_invoke(self):
        resp = requests.get("http://localhost:8999")
        assert resp.status_code == 200
        lambda_env = resp.json()
        assert "BUILDARG" in lambda_env
        assert lambda_env["BUILDARG"] == "present"
        assert "ENVVAR" in lambda_env
        assert lambda_env["ENVVAR"] == "present"
