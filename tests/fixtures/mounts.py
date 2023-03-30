import pytest
from sentential.lib.ontology import Ontology
from sentential.lib.mounts.aws_api_gateway import AwsApiGatewayMount

@pytest.fixture(scope="class")
def api_gateway_mount():
    return AwsApiGatewayMount(Ontology())