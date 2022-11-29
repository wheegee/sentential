from sentential.lib.drivers.aws_api_gateway import AwsApiGatewayDriver
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.exceptions import MountError
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Function
from sentential.lib.clients import clients

import sure  # type: ignore
import pytest

@pytest.fixture(scope="class")
def deployed(ontology: Ontology) -> Function:
    aws_lambda = AwsLambdaDriver(ontology)
    image = aws_lambda.image("0.0.1")
    return aws_lambda.deploy(image)

@pytest.mark.usefixtures("moto", "init", "ecr_images", "gw_domains", "deployed", "ontology")
class TestApiGatewayDriverPositive:
    def test_autocomplete(self):
        assert "dev.testing.io" in AwsApiGatewayDriver.autocomplete()

    def test_create_mount(self, ontology: Ontology, deployed: Function):
        aws_gw = AwsApiGatewayDriver(ontology, deployed)
        aws_gw.mount("dev.testing.io/api")
        mounts = aws_gw.mounts()
        all_mounts = aws_gw._all_mounts()
        autocompletions = aws_gw.autocomplete()

        # check mount() behavior
        mounts.should.contain("dev.testing.io/api")
        mounts.should_not.contain("dev.testing.io")

        # check autocomplete() behavior
        autocompletions.should.contain("dev.testing.io/api")
        autocompletions.should.contain("dev.testing.io")

        # check under the hood
        all_mounts = AwsApiGatewayDriver._all_mounts()
        all_mounts[0].should.have.property("DomainName").equal("dev.testing.io")
        all_mounts[0].should.have.property("Mappings").should_not.be.empty
        mapping = all_mounts[0].Mappings[0]
        mapping.should.have.property("Routes").should_not.be.empty
        route = mapping.Routes[0]
        route.should.have.property("RouteKey")
        route.should.have.property("Target")
        route.should.have.property("Integration")
        route.RouteKey.should.equal("ANY /api/{proxy+}")
        route.Target.should_not.be.none
        route.Integration.should.have.property("IntegrationId").should_not.be.none
        route.Target.should.contain(route.Integration.IntegrationId)

    def test_delete_mount(self, ontology: Ontology, deployed: Function):
        aws_gw = AwsApiGatewayDriver(ontology, deployed)
        aws_gw.umount("dev.testing.io/api")
        mounts = aws_gw.mounts()
        autocompletions = aws_gw.autocomplete()

        # check mount() behavior
        mounts.should.be.empty

        # checkout autocomplete behavior
        autocompletions.should.contain("dev.testing.io")
        autocompletions.should_not.contain("dev.testing.io/api")

@pytest.mark.usefixtures("moto", "init", "ecr_images", "deployed", "ontology")
class TestApiGatewayDriverNegative:
    def test_autocomplete(self):
        assert len(AwsApiGatewayDriver.autocomplete()) == 0
    
    def test_create_mount_path_dne(self, ontology: Ontology):
        aws_lambda = AwsLambdaDriver(ontology)
        image = aws_lambda.image("0.0.1")
        deployed = aws_lambda.deploy(image)
        aws_gw = AwsApiGatewayDriver(ontology, deployed)
        aws_gw.mount.when.called_with("dev.dne.io/api").should.have.raised(MountError)