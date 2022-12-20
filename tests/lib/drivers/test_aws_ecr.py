import pytest
import json
import requests_mock
import re
from tests.helpers import generate_image_manifest, generate_image_manifest_list
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.exceptions import AwsDriverError
from sentential.lib.clients import clients


@pytest.fixture(scope="class")
def mock_repo(ontology: Ontology):
    return clients.ecr.create_repository(
        repositoryName=ontology.context.repository_name
    )


@pytest.fixture(scope="class")
def mock_image_manifests():
    return [generate_image_manifest() for i in range(0, 5)]


@pytest.fixture(scope="class")
def mock_manifest_lists():
    return [generate_image_manifest_list() for i in range(0, 5)]


@pytest.fixture(scope="class")
def mock_images(mock_repo, mock_image_manifests):
    for idx, image_manifest in enumerate(mock_image_manifests):
        clients.ecr.put_image(
            repositoryName=mock_repo["repository"]["repositoryName"],
            imageManifest=json.dumps(image_manifest),
            imageTag=f"0.0.{idx}",
        )


@pytest.fixture(scope="class")
def mock_image_lists(mock_repo, mock_manifest_lists):
    for idx, manifests in enumerate(mock_manifest_lists):
        for image_manifest in manifests["image_manifests"]:
            clients.ecr.put_image(
                repositoryName=mock_repo["repository"]["repositoryName"],
                imageManifest=json.dumps(image_manifest),
            )

        clients.ecr.put_image(
            repositoryName=mock_repo["repository"]["repositoryName"],
            imageManifest=json.dumps(manifests["manifest_list"]),
            imageTag=f"0.1.{idx}",
        )


@pytest.fixture(scope="class")
def ecr(ontology: Ontology):
    with requests_mock.Mocker() as mock:
        blob_uri = re.compile(f"{ontology.context.ecr_rest_url}/blobs/.*")
        mock.get(blob_uri, json={"os": "linux", "architecture": "amd64"})
        yield AwsEcrDriver(ontology)


@pytest.mark.usefixtures("moto", "init", "ontology", "mock_images", "mock_image_lists")
class TestAwsEcrDriver:
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

    def test_image_count(self, ontology: Ontology, ecr: AwsEcrDriver):
        assert len(ecr.images()) == 15

    def test_image_by_tag(self, ecr: AwsEcrDriver):
        tag = self.get_tags()[0]
        image = ecr.image_by_tag(tag)
        assert tag in image.tags

    def test_image_by_tag_missing(self, ecr: AwsEcrDriver):
        with pytest.raises(AwsDriverError):
            ecr.image_by_tag("dne")

    def test_image_by_digest(self, ecr: AwsEcrDriver):
        digest = self.get_digests()[0]
        image = ecr.image_by_digest(digest)
        assert image.digest == digest

    def test_image_by_digest_missing(self, ecr: AwsEcrDriver):
        with pytest.raises(AwsDriverError):
            ecr.image_by_digest("dne")

    def test_image_by_id(self, ecr: AwsEcrDriver):
        id = self.get_ids()[0]
        image = ecr.image_by_id(id)
        assert image.id == id

    def test_image_by_id_missing(self, ecr: AwsEcrDriver):
        with pytest.raises(AwsDriverError):
            ecr.image_by_id("dne")
