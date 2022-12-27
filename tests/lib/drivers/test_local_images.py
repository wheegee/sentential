import pytest
from tests.helpers import rewrite
from sentential.lib.clients import clients
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.exceptions import LocalDriverError
from sentential.lib.shapes import Image


@pytest.mark.usefixtures(
    "moto", "init", "ontology", "mock_repo", "local_images_driver", "cwi"
)
class TestLocalImagesDriver:

    #
    # Test Helpers
    #

    def get_ecr_image_tags(self):
        images = clients.ecr.describe_images(repositoryName="test")["imageDetails"]
        image_tags = []
        for image in images:
            if "imageTags" in image:
                for tag in image["imageTags"]:
                    image_tags.append(tag)
        return image_tags

    #
    # Tests
    #

    def test_tag(self, cwi: Image):
        assert "cwi" in cwi.tags

    def test_digest(self, cwi: Image):
        assert cwi.digest is None

    def test_arch(self, cwi: Image):
        assert "amd" in cwi.arch or "arm" in cwi.arch

    def test_images(self, cwi: Image, local_images_driver: LocalImagesDriver):
        assert cwi in local_images_driver.images()

    def test_image_by_tag(self, local_images_driver: LocalImagesDriver, cwi: Image):
        assert local_images_driver.image_by_tag(cwi.tags[0]) == cwi

    def test_image_by_id(self, local_images_driver: LocalImagesDriver, cwi: Image):
        assert local_images_driver.image_by_id(cwi.id) == cwi

    def test_publish(self, local_images_driver: LocalImagesDriver):
        local_images_driver.publish("cwi", ["amd64", "arm64"])
        ecr_tags = self.get_ecr_image_tags()
        assert "cwi-amd64" in ecr_tags
        assert "cwi-arm64" in ecr_tags
        assert "cwi" in ecr_tags

    def test_clean(self, local_images_driver: LocalImagesDriver):
        local_images_driver.clean()
        assert len(local_images_driver.images()) == 0

    def test_block_publish_when_no_cwi(self, local_images_driver: LocalImagesDriver):
        local_images_driver.clean()
        with pytest.raises(LocalDriverError):
            local_images_driver.publish("latest", ["amd64"])

    def test_block_publish_when_cwi_differs(
        self, local_images_driver: LocalImagesDriver
    ):
        local_images_driver.build("amd64")
        rewrite(
            "Dockerfile",
            "# insert application specific build steps here",
            "RUN echo 123",
        )
        with pytest.raises(LocalDriverError):
            local_images_driver.publish("latest", ["amd64"])
