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
def cwi(init, ontology: Ontology):
    copyfile("./fixtures/app.py", f"{init}/src/app.py")
    local = LocalImagesDriver(ontology)
    return local.build()

@pytest.fixture(scope="class")
def local(ontology: Ontology):
    return LocalLambdaDriver(ontology)

@pytest.mark.usefixtures("moto", "init", "ontology", "cwi", "local")
class TestLocalLambdaDriver:
    def test_image_type(self, cwi: Image):
        assert isinstance(cwi, Image)

    def test_deploy(self, cwi: Image, local: LocalLambdaDriver):
        assert local.deploy(cwi) == cwi

    def test_invoke(self, cwi: Image, local: LocalLambdaDriver):
        local.deploy(cwi, {"AWS_ENDPOINT": "http://host.docker.internal:5000"})
        response = local.invoke("{}")
        assert response.StatusCode == 200
        assert "AWS_SESSION_TOKEN" in json.loads(response.Payload).keys()

    def test_destroy(self, cwi: Image, local: LocalLambdaDriver):
        local.destroy()
        locally_deployed_lambdas = [
            container.name == "sentential" for container in clients.docker.ps()
        ]
        assert not any(locally_deployed_lambdas)
