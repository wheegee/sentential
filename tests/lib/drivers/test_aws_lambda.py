from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Provision, Function
from sentential.lib.exceptions import AwsDriverError

import pytest

@pytest.mark.usefixtures("moto", "init", "ecr", "ontology")
class TestLambdaDriver:
    
    @pytest.fixture
    def driver(self, ontology: Ontology) -> AwsLambdaDriver:
        return AwsLambdaDriver(ontology)

    def test_provision(self, driver: AwsLambdaDriver):
        assert isinstance(driver.provision, Provision)
    
    def test_deployed(self, driver: AwsLambdaDriver):
        with pytest.raises(AwsDriverError):
            driver.deployed()

    def test_images(self, driver: AwsLambdaDriver):
        versions = [ image.versions for image in driver.images() ]
        versions = sum(versions, []) # flatten
        assert versions == ["0.0.1", "0.0.2","0.1.0","0.1.1","1.0.0"]

    def test_image(self, driver: AwsLambdaDriver):
        image = driver.image("0.0.1")
        assert "0.0.1" in image.versions
    
    def test_deploy(self, driver: AwsLambdaDriver):
        image = driver.image("0.0.2")
        deployed = driver.deploy(image)
        assert "0.0.2" in deployed.image.versions

    def test_destroy(self, driver: AwsLambdaDriver):
        deployed = driver.deployed()
        driver.destroy(deployed)

