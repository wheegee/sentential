import pytest
import json

from sentential.lib.ontology import Ontology
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.exceptions import AwsDriverError
from sentential.lib.clients import clients
from sentential.lib.shapes import AwsManifestList


@pytest.mark.usefixtures("moto", "init", "ontology", "mock_repo", "aws_ecr_driver")
class TestAwsEcrDriver:
    def test_image_count(self, aws_ecr_driver: AwsEcrDriver):
        assert len(aws_ecr_driver._manifest_lists()) == 4

    def test_get_image_implicit(self, aws_ecr_driver: AwsEcrDriver):
        image = aws_ecr_driver.get_image()
        assert image.imageId.imageTag == "0.0.3"

    def test_get_image_explicit(self, aws_ecr_driver: AwsEcrDriver):
        image = aws_ecr_driver.get_image("0.0.1")
        assert isinstance(image.imageManifest, AwsManifestList)
        assert image.imageId.imageTag == "0.0.1"

    def test_get_image_missing(self, aws_ecr_driver: AwsEcrDriver):
        with pytest.raises(AwsDriverError):
            aws_ecr_driver.get_image("3.1.4")
    
    def test_get_next_build(self, aws_ecr_driver: AwsEcrDriver):
        assert "0.0.4" == aws_ecr_driver.next()

    def test_get_next_minor(self, aws_ecr_driver: AwsEcrDriver):
        assert "0.1.0" == aws_ecr_driver.next(False, True)
    
    def test_get_next_major(self, aws_ecr_driver: AwsEcrDriver):
        assert "1.0.0" == aws_ecr_driver.next(True, False)

    def test_clean(self, aws_ecr_driver: AwsEcrDriver):
        aws_ecr_driver.clean()
        with pytest.raises(AwsDriverError):
            aws_ecr_driver.get_image()
