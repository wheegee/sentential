import pytest
from sentential.lib.mounts.aws_api_gateway import AwsApiGatewayMount
from sentential.lib.mounts.aws_api_gateway import proxify, deproxify
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.shapes import Architecture


class TestAwsApiGatewayMountHelpers:
    def test_proxify(self):
        assert proxify("https://a.com/{proxy+}") == "https://a.com/{proxy+}"
        assert proxify("https://a.com") == "https://a.com/{proxy+}"
        assert proxify("https://a.com/") == "https://a.com/{proxy+}"
        assert proxify("https://a.com") == "https://a.com/{proxy+}"

    def test_deproxify(self):
        assert deproxify("https://a.com/{proxy+}") == "https://a.com/"
        assert deproxify("https://a.com/{proxy}") == "https://a.com/"
        assert deproxify("https://a.com/") == "https://a.com/"
        assert deproxify("https://a.com") == "https://a.com/"


# TODO: add state tests for lambda perms, integrations and ?... surrounding both mount/umount
# TODO: make PR against moto to correction behavior of redundant route creation (moto should throw, it does not)
@pytest.mark.usefixtures(
    "moto",
    "init",
    "ontology",
    "mock_repo",
    "mock_api_gateway",
    "api_gateway_mount",
    "aws_ecr_driver",
    "aws_lambda_driver",
)
class TestAwsApiGatewayMount:
    def test_autocomplete(self, api_gateway_mount: AwsApiGatewayMount):
        assert len(AwsApiGatewayMount.autocomplete()) == 1

    def test_mount(
        self,
        api_gateway_mount: AwsApiGatewayMount,
        aws_ecr_driver: AwsEcrDriver,
        aws_lambda_driver: AwsLambdaDriver,
    ):
        image = aws_ecr_driver.get_image()
        aws_lambda_driver.deploy(image, Architecture.system())
        function_name = aws_lambda_driver.ontology.context.resource_name
        function_arn = aws_lambda_driver.ontology.context.resource_arn
        host = AwsApiGatewayMount.autocomplete()[0]
        api_gateway_mount.mount(host)
        assert f"{host}/" in api_gateway_mount.mounts()

    def test_subroute_v1_mount(self, api_gateway_mount: AwsApiGatewayMount):
        host = AwsApiGatewayMount.autocomplete()[0]
        api_gateway_mount.mount(f"{host}/v1")
        assert f"{host}/v1/" in api_gateway_mount.mounts()

    def test_subroute_v2_mount(self, api_gateway_mount: AwsApiGatewayMount):
        host = AwsApiGatewayMount.autocomplete()[0]
        api_gateway_mount.mount(f"{host}/v2")
        assert f"{host}/v2/" in api_gateway_mount.mounts()

    def test_umount_single_route(self, api_gateway_mount: AwsApiGatewayMount):
        host = AwsApiGatewayMount.autocomplete()[0]
        api_gateway_mount.umount(f"{host}/v2")
        assert f"{host}/v2/" not in api_gateway_mount.mounts()
        assert len(api_gateway_mount.mounts()) == 2

    def test_umount_all_routes(self, api_gateway_mount: AwsApiGatewayMount):
        api_gateway_mount.umount()
        assert len(api_gateway_mount.mounts()) == 0
