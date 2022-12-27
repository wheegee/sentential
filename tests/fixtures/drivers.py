import pytest
from pytest import MonkeyPatch
import re
import requests_mock
from tests.mockery.docker import push_mock, manifest_create_mock, manifest_push_mock
from tests.mockery.ecr_api import get_blob
from sentential.lib.ontology import Ontology
from sentential.lib.clients import clients
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver

@pytest.fixture(scope="class")
def aws_ecr_driver():
    ontology = Ontology()
    with requests_mock.Mocker() as mock:
        blob_uri = re.compile(f"{ontology.context.ecr_rest_url}/blobs/.*")
        mock.get(blob_uri, json={"os": "linux", "architecture": "arm64"})
        yield AwsEcrDriver(ontology)

@pytest.fixture(scope="class")
def aws_lambda_driver():
    return AwsLambdaDriver(Ontology())

@pytest.fixture(scope="class")
def local_images_driver():
    monkeypatch = MonkeyPatch() 
    monkeypatch.setattr(clients.docker, 'push', push_mock)
    monkeypatch.setattr(clients.docker.manifest, "create", manifest_create_mock)
    monkeypatch.setattr(clients.docker.manifest, 'push', manifest_push_mock)
    return LocalImagesDriver(Ontology())

@pytest.fixture(scope="class")
def local_lambda_driver():
    return LocalLambdaDriver(Ontology())

