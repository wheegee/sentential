from typing import cast
import pytest
import json
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.shapes import AwsImageManifest, AwsManifestList
from tests.helpers import generate_image_manifest, generate_image_manifest_list

#
# Current Working Image
#


@pytest.fixture(scope="class")
def cwi():
    local_images_driver = LocalImagesDriver(Ontology())
    return local_images_driver.build("amd64")


#
# ECR Mock Fixtures
#


def populate_mock_images(repo_name, quantity):
    mock_image_manifests = [generate_image_manifest() for i in range(0, quantity - 1)]
    for idx, image_manifest in enumerate(mock_image_manifests):
        clients.ecr.put_image(
            repositoryName=repo_name,
            imageManifest=json.dumps(image_manifest.dict()),
            imageTag=f"0.0.{idx}",
        )


def populate_mock_image_lists(repo_name, quantity):
    # These images are added without tags, then the manifest list is tagged.
    # Sentential tags the images with {repo_name}-{arch}, so this is slightly
    # divergent from a #publish operation, but still valid ecr state.
    mock_manifest_lists = [
        generate_image_manifest_list() for i in range(0, quantity - 1)
    ]
    for idx, manifests in enumerate(mock_manifest_lists):
        for image_manifest in manifests["image_manifests"]:
            image_manifest = cast(AwsImageManifest, image_manifest)
            clients.ecr.put_image(
                repositoryName=repo_name,
                imageManifest=json.dumps(image_manifest.dict()),
            )

        manifest_list = cast(AwsManifestList, manifests["manifest_list"])
        clients.ecr.put_image(
            repositoryName=repo_name,
            imageManifest=json.dumps(manifest_list.dict()),
            imageTag=f"0.1.{idx}",
        )


@pytest.fixture(scope="class")
def mock_repo(ontology: Ontology):
    repo_name = ontology.context.repository_name
    clients.ecr.create_repository(repositoryName=repo_name)
    populate_mock_images(repo_name, 6)
    populate_mock_image_lists(repo_name, 6)
