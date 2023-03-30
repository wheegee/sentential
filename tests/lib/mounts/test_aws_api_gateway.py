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
        assert deproxify("https://a.com") == "https://a.com"

@pytest.mark.usefixtures(
    "moto", "init", "ontology", "mock_repo", "mock_api_gateway", "api_gateway_mount", "aws_ecr_driver", "aws_lambda_driver"
)
class TestAwsApiGatewayMount:
    def test_autocomplete(self, api_gateway_mount: AwsApiGatewayMount):
        assert len(AwsApiGatewayMount.autocomplete()) == 1

    def test_mount(self, api_gateway_mount: AwsApiGatewayMount, aws_ecr_driver: AwsEcrDriver, aws_lambda_driver: AwsLambdaDriver):
        image = aws_ecr_driver.get_image()
        aws_lambda_driver.deploy(image, Architecture.system())
        function_name = aws_lambda_driver.ontology.context.resource_name
        function_arn = aws_lambda_driver.ontology.context.resource_arn
        url = AwsApiGatewayMount.autocomplete()[0]
        api_gateway_mount.mount(url)
        assert f"{url}/" in api_gateway_mount.mounts()

    def test_umount(self, api_gateway_mount: AwsApiGatewayMount):
        api_gateway_mount.umount()
        assert len(api_gateway_mount.mounts()) == 0
