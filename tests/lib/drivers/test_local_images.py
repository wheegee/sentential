import pytest
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.exceptions import LocalDriverError
from sentential.lib.shapes import Image
from tests.helpers import rewrite


@pytest.fixture(scope="class")
def local_images(ontology: Ontology):
    yield LocalImagesDriver(ontology)


@pytest.fixture(scope="class")
def cwi(local_images):
    yield local_images.build()
    local_images.clean()


@pytest.mark.usefixtures("moto", "init", "ontology", "local_images", "cwi")
class TestLocalImagesDriver:
    def test_build_return_type(self, cwi: Image):
        assert isinstance(cwi, Image)

    def test_images(self, cwi: Image, local_images: LocalImagesDriver):
        assert len(local_images.images()) == 1
        assert cwi in local_images.images()

    def test_tag(self, cwi: Image):
        assert "cwi" in cwi.tags

    def test_digest(self, cwi: Image):
        assert cwi.digest is None

    def test_arch(self, cwi: Image):
        assert "amd" in cwi.arch or "arm" in cwi.arch

    def test_image_by_tag(self, local_images: LocalImagesDriver, cwi: Image):
        assert local_images.image_by_tag(cwi.tags[0]) == cwi

    def test_image_by_id(self, local_images: LocalImagesDriver, cwi: Image):
        assert local_images.image_by_id(cwi.id) == cwi

    def test_clean(self, local_images: LocalImagesDriver):
        local_images.clean()
        assert len(local_images.images()) == 0

    def test_block_publish_when_no_cwi(
        self, cwi: Image, local_images: LocalImagesDriver
    ):
        local_images.clean()
        with pytest.raises(LocalDriverError):
            local_images.publish("latest", True)

    def test_block_publish_when_cwi_differs(
        self, cwi: Image, local_images: LocalImagesDriver
    ):
        local_images.build()
        rewrite(
            "Dockerfile",
            "# insert application specific build steps here",
            "RUN echo 123",
        )
        with pytest.raises(LocalDriverError):
            local_images.publish("latest", False)
