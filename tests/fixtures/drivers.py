import pytest
from pytest import MonkeyPatch
import re
import requests_mock
from tests.stubs.docker import push_stub, manifest_create_stub, manifest_push_stub
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
        mock.get(blob_uri, json={"os": "linux", "architecture": "amd64"})
        yield AwsEcrDriver(ontology)

@pytest.fixture(scope="class")
def aws_lambda_driver():
    return AwsLambdaDriver(Ontology())

@pytest.fixture(scope="class")
def local_images_driver():
    monkeypatch = MonkeyPatch() 
    monkeypatch.setattr(clients.docker, 'push', push_stub)
    monkeypatch.setattr(clients.docker.manifest, "create", manifest_create_stub)
    monkeypatch.setattr(clients.docker.manifest, 'push', manifest_push_stub)
    return LocalImagesDriver(Ontology())

@pytest.fixture(scope="class")
def local_lambda_driver():
    return LocalLambdaDriver(Ontology())

