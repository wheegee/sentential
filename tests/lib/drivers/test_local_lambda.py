import json
import pytest
from os import environ
from shutil import copyfile
from python_on_whales.components.image.cli_wrapper import Image
from sentential.lib.clients import clients
from sentential.lib.shapes import Architecture, LambdaInvokeResponse
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.drivers.local_images import LocalImagesDriver
from tests.helpers import rewrite


@pytest.fixture(scope="class")
def hander_returns_environ(init):
    copyfile("./fixtures/app.py", f"{init}/src/app.py")
    rewrite(
        "Dockerfile",
        "# insert application specific build steps here",
        "ARG buildarg\nENV BUILDARG=$buildarg",
    )


@pytest.mark.usefixtures(
    "moto",
    "init",
    "hander_returns_environ",
    "local_lambda_driver",
    "local_images_driver",
)
class TestLocalLambdaDriver:
    def test_build(
        self,
        local_images_driver: LocalImagesDriver,
    ):
        local_images_driver.ontology.args.write("buildarg", ["present"])
        local_images_driver.build(Architecture.system())

    def test_deploy(
        self,
        local_images_driver: LocalImagesDriver,
        local_lambda_driver: LocalLambdaDriver,
    ):
        cwi = local_images_driver.get_image()
        local_lambda_driver.ontology.envs.write("ENVVAR", ["present"])
        message = local_lambda_driver.deploy(
            cwi,
            {"AWS_ENDPOINT": "http://host.docker.internal:5000"},
        )
        assert "AKIAIOSFODNN7EXAMPLE-test" in message

    def test_invoke(self, local_lambda_driver: LocalLambdaDriver):
        response = json.loads(local_lambda_driver.invoke("{}"))
        response = LambdaInvokeResponse(**response)
        assert response.StatusCode == 200
        lambda_env = json.loads(response.Payload)
        assert "AWS_SESSION_TOKEN" in lambda_env.keys()
        assert "BUILDARG" in lambda_env.keys()
        assert lambda_env["BUILDARG"] == "present"
        assert "ENVVAR" in lambda_env.keys()
        assert lambda_env["ENVVAR"] == "present"

    def test_destroy(self, local_lambda_driver: LocalLambdaDriver):
        local_lambda_driver.destroy()
        locally_deployed_lambdas = [
            container.name == "sentential" for container in clients.docker.ps()
        ]
        assert not any(locally_deployed_lambdas)
