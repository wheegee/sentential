import pytest
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.local_images import LocalImagesDriver

@pytest.fixture(scope="class")
def ontology():
    return Ontology()

@pytest.fixture(scope="class")
def cwi():
    local_images_driver = LocalImagesDriver(Ontology())
    return local_images_driver.build("amd64")