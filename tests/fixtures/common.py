from ast import List
from typing import cast
import pytest
import json
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.shapes import AwsImageDetail, Architecture
from tests.helpers import generate_image_manifest, generate_image_manifest_list

#
# Current Working Image
#


@pytest.fixture(scope="class")
def cwi():
    local_images_driver = LocalImagesDriver(Ontology())
    local_images_driver.clean()
    yield local_images_driver.build(Architecture.system())


#
# ECR Mock Fixtures
#


def popluate_mock_images(repo_name):
    image_pairs = []
    for build in range(0, 4):
        image_pair = []
        for arch in ["amd64", "arm64"]:
            image_manifest = generate_image_manifest()
            resp = clients.ecr.put_image(
                repositoryName=repo_name,
                imageManifest=json.dumps(image_manifest.dict()),
                imageTag=f"0.0.{build}-{arch}",
            )
            image_pair.append(AwsImageDetail(**resp["image"]))

        image_pairs.append(image_pair)

    for build, image_pair in enumerate(image_pairs):
        manifest_list = generate_image_manifest_list(image_pair)

        clients.ecr.put_image(
            repositoryName=repo_name,
            imageManifest=json.dumps(manifest_list.dict()),
            imageTag=f"0.0.{build}",
        )


@pytest.fixture(scope="class")
def mock_repo(ontology: Ontology):
    repo_name = ontology.context.repository_name
    clients.ecr.create_repository(repositoryName=repo_name)
    popluate_mock_images(repo_name)
