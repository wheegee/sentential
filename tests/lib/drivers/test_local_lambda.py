import json
import pytest
from shutil import copyfile
from sentential.lib.clients import clients
from sentential.lib.shapes import Image
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.local_lambda import LocalLambdaDriver

@pytest.fixture(scope="class")
def hander_returns_environ(init):
    copyfile("./fixtures/app.py", f"{init}/src/app.py")

@pytest.mark.usefixtures(
    "moto", "init", "hander_returns_environ", "cwi", "local_lambda_driver", "local_images_driver"
)
class TestLocalLambdaDriver:
    def test_deploy(self, cwi: Image, local_lambda_driver: LocalLambdaDriver):
        assert local_lambda_driver.deploy(cwi) == cwi

    def test_invoke(
        self, cwi: Image, local_lambda_driver: LocalLambdaDriver
    ):
        envs = local_lambda_driver.ontology.envs
        envs.write("HELLO", ["THIS_IS_ENV"])
        local_lambda_driver.deploy(cwi, {"AWS_ENDPOINT": "http://host.docker.internal:5000"})
        response = local_lambda_driver.invoke("{}")
        assert response.StatusCode == 200
        lambda_env = json.loads(response.Payload)
        assert "AWS_SESSION_TOKEN" in lambda_env.keys()
        assert "HELLO" in lambda_env.keys()
        assert lambda_env["HELLO"] == "THIS_IS_ENV"

    def test_destroy(self, local_lambda_driver: LocalLambdaDriver):
        local_lambda_driver.destroy()
        locally_deployed_lambdas = [
            container.name == "sentential" for container in clients.docker.ps()
        ]
        assert not any(locally_deployed_lambdas)
