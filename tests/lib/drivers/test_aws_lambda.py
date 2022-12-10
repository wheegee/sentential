from typing import cast
import pytest
from sentential.lib.shapes import Provision
from tests.lib.drivers.test_aws_ecr import ecr, mock_repo, mock_image_manifests, mock_manifest_lists, mock_images, mock_image_lists

from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.exceptions import AwsDriverError, AWS_EXCEPTIONS

@pytest.fixture(scope="class")
def lmb(ontology: Ontology):
    return AwsLambdaDriver(ontology)

@pytest.mark.usefixtures("moto", "init", "ontology", "mock_images", "mock_manifest_lists")
class TestAwsLambdaDriver:
    def get_lambda(self, ontology: Ontology):
        return clients.lmb.get_function(FunctionName=ontology.context.resource_name)

    def get_lambda_config(self, ontology: Ontology):
        return clients.lmb.get_function_configuration(FunctionName=ontology.context.resource_name)

    def test_deploy(self, ecr: AwsEcrDriver, lmb: AwsLambdaDriver, ontology: Ontology):
        image = ecr.image_by_tag("0.0.1")
        lmb.deploy(image)
        deployed_digest = self.get_lambda(ontology)["Configuration"]["CodeSha256"]
        assert image.digest == f"sha256:{deployed_digest}"

    def test_destroy(self, lmb: AwsLambdaDriver, ontology: Ontology):
        lmb.destroy()
        with pytest.raises(AWS_EXCEPTIONS): # this is a tad lame
            self.get_lambda(ontology)

    def test_deploy_w_provisions(self, ecr: AwsEcrDriver, lmb: AwsLambdaDriver, ontology: Ontology):
        # TODO: StorageSize seems to be missing from moto mock response...
        # ontology.configs.write("storage", [storage])
        ontology.configs.write("memory", ["2048"])
        ontology.configs.write("timeout", ["25"])
        ontology.configs.write("subnet_ids", ["sn-123", "sn-456"])
        ontology.configs.write("security_group_ids", ["sg-123", "sg-456"])

        image = ecr.image_by_tag("0.0.1")
        lmb.deploy(image)

        lambda_config = self.get_lambda_config(ontology)
        ssm_config = cast(Provision, ontology.configs.parameters)
        
        assert lambda_config['MemorySize'] == ssm_config.memory
        assert lambda_config['Timeout'] == ssm_config.timeout
        assert lambda_config['VpcConfig']['SubnetIds'] == ssm_config.subnet_ids
        assert lambda_config['VpcConfig']['SecurityGroupIds'] == ssm_config.security_group_ids
