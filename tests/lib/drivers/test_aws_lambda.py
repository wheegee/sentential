import pytest
from tests.lib.drivers.test_aws_ecr import (
    ecr,
    mock_repo,
    mock_image_manifests,
    mock_manifest_lists,
    mock_images,
    mock_image_lists,
)

from sentential.lib.ontology import Ontology
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.exceptions import AwsDriverError


@pytest.fixture(scope="class")
def lmb(ontology: Ontology):
    return AwsLambdaDriver(ontology)


@pytest.mark.usefixtures(
    "moto", "init", "ontology", "mock_images", "mock_manifest_lists"
)
class TestAwsLambdaDriver:
    def test_deploy(self, ecr: AwsEcrDriver, lmb: AwsLambdaDriver):
        """did an image fetch / deploy and got some weird error, might be a bug"""
        pass
