import pytest
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.shapes import Image


@pytest.fixture(scope="class")
def local(ontology: Ontology):
    local = LocalImagesDriver(ontology)
    return local

@pytest.fixture(scope="class")
def cwi(local):
    yield local.build()


@pytest.mark.usefixtures("moto", "init", "ontology", "local", "cwi")
class TestLocalImagesDriver:
    def test_build_return_type(self, cwi: Image):
        assert isinstance(cwi, Image)

    def test_images(self, local: LocalImagesDriver, cwi: Image):
        assert len(local.images()) == 1
        assert cwi in local.images()

    def test_tag(self, cwi: Image):
        assert "cwi" in cwi.tags

    def test_digest(self, cwi: Image):
        assert cwi.digest is None

    def test_arch(self, cwi: Image):
        assert "amd" in cwi.arch or "arm" in cwi.arch

    def test_image_by_tag(self, local: LocalImagesDriver, cwi: Image):
        assert local.image_by_tag(cwi.tags[0]) == cwi

    def test_image_by_id(self, local: LocalImagesDriver, cwi: Image):
        assert local.image_by_id(cwi.id) == cwi

    def test_clean(self, local: LocalImagesDriver):
        local.clean()
        assert len(local.images()) == 0
