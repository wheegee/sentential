import json
import pytest
from shutil import copyfile
from sentential.lib.clients import clients
from sentential.lib.shapes import Image
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver


@pytest.fixture(scope="class")
def local_lambda(ontology: Ontology):
    yield LocalLambdaDriver(ontology)


@pytest.fixture(scope="class")
def local_images(ontology: Ontology):
    yield LocalImagesDriver(ontology)


@pytest.fixture(scope="class")
def hander_returns_environ(init):
    copyfile("./fixtures/app.py", f"{init}/src/app.py")


@pytest.fixture(scope="class")
def cwi(local_images: LocalImagesDriver):
    yield local_images.build()
    local_images.clean()


@pytest.mark.usefixtures(
    "moto", "init", "hander_returns_environ", "ontology", "cwi", "local_lambda"
)
class TestLocalLambdaDriver:
    def test_image_type(self, cwi: Image):
        assert isinstance(cwi, Image)

    def test_deploy(self, cwi: Image, local_lambda: LocalLambdaDriver):
        assert local_lambda.deploy(cwi) == cwi

    def test_invoke(
        self, cwi: Image, ontology: Ontology, local_lambda: LocalLambdaDriver
    ):
        ontology.envs.write("HELLO", ["THIS_IS_ENV"])
        local_lambda.deploy(cwi, {"AWS_ENDPOINT": "http://host.docker.internal:5000"})
        response = local_lambda.invoke("{}")
        assert response.StatusCode == 200
        lambda_env = json.loads(response.Payload)
        assert "AWS_SESSION_TOKEN" in lambda_env.keys()
        assert "HELLO" in lambda_env.keys()
        assert lambda_env["HELLO"] == "THIS_IS_ENV"

    def test_destroy(self, local_lambda: LocalLambdaDriver):
        local_lambda.destroy()
        locally_deployed_lambdas = [
            container.name == "sentential" for container in clients.docker.ps()
        ]
        assert not any(locally_deployed_lambdas)
