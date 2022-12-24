import pytest
import json

from sentential.lib.ontology import Ontology
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.exceptions import AwsDriverError
from sentential.lib.clients import clients

@pytest.mark.usefixtures("moto", "init", "ontology", "mock_repo", "aws_ecr_driver")
class TestAwsEcrDriver:
    #
    # Test Helpers
    #

    def get_digests(self):
        images = clients.ecr.list_images(repositoryName="test")["imageIds"]
        return [i["imageDigest"] for i in images]

    def get_tags(self):
        images = clients.ecr.list_images(repositoryName="test")["imageIds"]
        return [i["imageTag"] for i in images if "imageTag" in i]

    def get_ids(self):
        images = clients.ecr.list_images(repositoryName="test")["imageIds"]
        query = [{"imageDigest": i["imageDigest"]} for i in images]
        details = clients.ecr.batch_get_image(repositoryName="test", imageIds=query)[
            "images"
        ]
        manifests = [json.loads(manifest["imageManifest"]) for manifest in details]
        return [i["config"]["digest"] for i in manifests if "config" in i]

    #
    # Tests
    #

    def test_image_count(self, aws_ecr_driver: AwsEcrDriver):
        assert len(aws_ecr_driver.images()) == 15

    def test_image_by_tag(self, aws_ecr_driver: AwsEcrDriver):
        tag = self.get_tags()[0]
        image = aws_ecr_driver.image_by_tag(tag)
        assert tag in image.tags

    def test_image_by_tag_missing(self, aws_ecr_driver: AwsEcrDriver):
        with pytest.raises(AwsDriverError):
            aws_ecr_driver.image_by_tag("dne")

    def test_image_by_digest(self, aws_ecr_driver: AwsEcrDriver):
        digest = self.get_digests()[0]
        image = aws_ecr_driver.image_by_digest(digest)
        assert image.digest == digest

    def test_image_by_digest_missing(self, aws_ecr_driver: AwsEcrDriver):
        with pytest.raises(AwsDriverError):
            aws_ecr_driver.image_by_digest("dne")

    def test_image_by_id(self, aws_ecr_driver: AwsEcrDriver):
        id = self.get_ids()[0]
        image = aws_ecr_driver.image_by_id(id)
        assert image.id == id

    def test_image_by_id_missing(self, aws_ecr_driver: AwsEcrDriver):
        with pytest.raises(AwsDriverError):
            aws_ecr_driver.image_by_id("dne")
