from sentential.lib.drivers.aws_api_gateway import AwsApiGatewayDriver
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.ontology import Ontology

import pytest

@pytest.mark.usefixtures("moto", "init", "ecr", "ontology", "apigateway")
class TestApiGatewayDriver:
    def test_autocomplete(self):
        assert "dev.testing.io" in AwsApiGatewayDriver.autocomplete()

    def test_create_route(self, ontology: Ontology):
        aws_lambda = AwsLambdaDriver(ontology)
        image = aws_lambda.image("0.0.1")
        deployed = aws_lambda.deploy(image)

        aws_gw = AwsApiGatewayDriver(ontology, deployed)
        aws_gw.mount("dev.testing.io/api")
        assert "dev.testing.io/api" in aws_gw.autocomplete()

    def test_delete_route(self, ontology: Ontology):
        aws_lambda = AwsLambdaDriver(ontology)
        deployed = aws_lambda.deployed()

        aws_gw = AwsApiGatewayDriver(ontology, deployed)
        aws_gw.umount("dev.testing.io/api")
        assert "dev.testing.io/api" not in aws_gw.autocomplete()