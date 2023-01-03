import pytest
from typing import cast
from sentential.lib.shapes import Provision, Architecture
from sentential.lib.clients import clients
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.exceptions import AWS_EXCEPTIONS


@pytest.mark.usefixtures(
    "moto", "init", "ontology", "mock_repo", "aws_lambda_driver", "aws_ecr_driver"
)
class TestAwsLambdaDriver:
    def get_lambda(self, function_name: str):
        return clients.lmb.get_function(FunctionName=function_name)

    def get_lambda_config(self, function_name: str):
        return clients.lmb.get_function_configuration(FunctionName=function_name)

    def test_deploy(
        self, aws_lambda_driver: AwsLambdaDriver, aws_ecr_driver: AwsEcrDriver
    ):
        image = aws_ecr_driver.get_image()
        aws_lambda_driver.deploy(image, Architecture.system().value)
        function_name = aws_lambda_driver.ontology.context.resource_name
        deployed_digest = self.get_lambda(function_name)["Configuration"]["CodeSha256"]
        image.imageManifest
        arch_digest = {
            f"{manifest.platform.architecture}": manifest.digest
            for manifest in image.imageManifest.manifests
        }
        assert f"sha256:{deployed_digest}" == arch_digest[Architecture.system().value]

    def test_destroy(self, aws_lambda_driver: AwsLambdaDriver):
        aws_lambda_driver.destroy()
        function_name = aws_lambda_driver.ontology.context.resource_name
        with pytest.raises(AWS_EXCEPTIONS):  # this is a tad lame
            self.get_lambda(function_name)

    def test_deploy_w_provisions(
        self, aws_lambda_driver: AwsLambdaDriver, aws_ecr_driver: AwsEcrDriver
    ):
        # TODO: StorageSize seems to be missing from moto mock response...
        # ontology.configs.write("storage", [storage])
        function_name = aws_lambda_driver.ontology.context.resource_name
        configs = aws_lambda_driver.ontology.configs
        configs.write("memory", ["2048"])
        configs.write("timeout", ["25"])
        configs.write("subnet_ids", ["sn-123", "sn-456"])
        configs.write("security_group_ids", ["sg-123", "sg-456"])

        image = aws_ecr_driver.get_image("0.0.1")
        aws_lambda_driver.deploy(image, Architecture.system().value)

        lambda_config = self.get_lambda_config(function_name)
        ssm_config = cast(Provision, configs.parameters)

        assert lambda_config["MemorySize"] == ssm_config.memory
        assert lambda_config["Timeout"] == ssm_config.timeout
        assert lambda_config["VpcConfig"]["SubnetIds"] == ssm_config.subnet_ids
        assert (
            lambda_config["VpcConfig"]["SecurityGroupIds"]
            == ssm_config.security_group_ids
        )
