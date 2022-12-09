import pytest
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.exceptions import LocalDriverError
from sentential.lib.shapes import Image

@pytest.fixture(scope="class")
def local(ontology: Ontology):
    local = LocalImagesDriver(ontology)
    local.clean()
    return local

@pytest.fixture(scope="class")
def image(local):
    yield local.build("0.0.1")

@pytest.mark.usefixtures("moto", "init", "ontology", "local", "image")
class TestLocalImagesDriver:
    def test_build_return_type(self, image: Image):
        assert isinstance(image, Image)
    
    def test_images(self, local: LocalImagesDriver, image: Image):
        assert len(local.images()) == 1
        assert image in local.images()

    def test_tag(self, local: LocalImagesDriver, image: Image):
        assert "0.0.1" in image.tags
    
    def test_digest(self, local: LocalImagesDriver, image: Image):
        assert image.digest is None
    
    def test_arch(self, local: LocalImagesDriver, image: Image):
        assert ("amd" in image.arch or "arm" in image.arch)
    
    def test_image_by_tag(self, local: LocalImagesDriver, image: Image):
        assert local.image_by_tag(image.tags[0]) == image

    def test_image_by_id(self, local: LocalImagesDriver, image: Image):
        assert local.image_by_id(image.id) == image

    def test_clean(self, local: LocalImagesDriver):
        local.clean()
        assert len(local.images()) == 0