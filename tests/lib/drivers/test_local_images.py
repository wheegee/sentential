import pytest
from tests.helpers import rewrite
from sentential.lib.clients import clients
from sentential.lib.exceptions import LocalDriverError
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.shapes import Architecture
from python_on_whales.components.image.cli_wrapper import Image


@pytest.fixture(scope="class")
def cross_arch() -> Architecture:
    cross_arch = [a for a in Architecture]
    host_arch_index = cross_arch.index(Architecture.system())
    del cross_arch[host_arch_index]
    return cross_arch[0]


@pytest.fixture(scope="class")
def native_arch() -> Architecture:
    return Architecture.system()


@pytest.mark.usefixtures(
    "moto",
    "init",
    "ontology",
    "cwi",
    "mock_repo",
    "local_images_driver",
    "native_arch",
    "cross_arch",
)
class TestLocalImagesDriver:
    def test_get_image(self, cwi: Image, local_images_driver: LocalImagesDriver):
        assert local_images_driver.get_image() == cwi

    def test_publish(
        self, cwi: Image, local_images_driver: LocalImagesDriver, native_arch
    ):
        assert cwi in local_images_driver.publish("1.0.0", [native_arch])

    def test_publish_multi_arch(
        self, cwi: Image, local_images_driver: LocalImagesDriver
    ):
        built = local_images_driver.publish("2.0.0", [a for a in Architecture])
        archs = [image.architecture for image in built]
        assert len(archs) == 2
        assert "amd64" in archs
        assert "arm64" in archs
        assert cwi in built

    def test_cross_build(self, local_images_driver: LocalImagesDriver, cross_arch):
        assert (
            local_images_driver.build(cross_arch, False).architecture
            == cross_arch.value
        )

    def test_cross_publish_failure(
        self, local_images_driver: LocalImagesDriver, native_arch
    ):
        with pytest.raises(LocalDriverError):
            local_images_driver.publish("1.0.1", [native_arch])

    def test_cross_publish(self, local_images_driver: LocalImagesDriver, cross_arch):
        built = local_images_driver.publish("1.0.1", [cross_arch])
        archs = [image.architecture for image in built]
        assert len(archs) == 1
        assert cross_arch.value in archs

    def test_clean(self, local_images_driver: LocalImagesDriver):
        local_images_driver.clean()
        with pytest.raises(LocalDriverError):
            local_images_driver.get_image()
