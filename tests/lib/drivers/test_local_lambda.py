import json
import pytest
from shutil import copyfile
from sentential.lib.clients import clients
from sentential.lib.shapes import Image
from sentential.lib.ontology import Ontology
from sentential.lib.exceptions import LocalDriverError
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver


@pytest.fixture(scope="class")
def image(init, ontology: Ontology):
    copyfile("./fixtures/app.py", f"{init}/src/app.py")
    local = LocalImagesDriver(ontology)
    local.clean()
    return local.build("0.0.1")


@pytest.fixture(scope="class")
def local(ontology: Ontology):
    return LocalLambdaDriver(ontology)


@pytest.mark.usefixtures("moto", "init", "ontology", "image", "local")
class TestLocalLambdaDriver:
    def test_image_type(self, image: Image):
        assert isinstance(image, Image)

    def test_deploy(self, image: Image, local: LocalLambdaDriver):
        assert local.deploy(image) == image

    def test_invoke(self, image: Image, local: LocalLambdaDriver):
        local.deploy(image, {"AWS_ENDPOINT": "http://host.docker.internal:5000"})
        response = local.invoke("{}")
        assert response.StatusCode == 200
        assert "AWS_SESSION_TOKEN" in json.loads(response.Payload).keys()

    def test_destroy(self, image: Image, local: LocalLambdaDriver):
        local.destroy()
        locally_deployed_lambdas = [
            container.name == "sentential" for container in clients.docker.ps()
        ]
        assert not any(locally_deployed_lambdas)
