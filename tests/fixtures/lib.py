import pytest
from pytest import MonkeyPatch
from sentential.lib.ontology import Ontology
from sentential.lib.joinery import Joinery
from tests.fixtures.drivers import local_images_driver, aws_ecr_driver
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver


@pytest.fixture(scope="class")
def ontology():
    return Ontology()


@pytest.fixture(scope="class")
def joinery(local_images_driver: LocalImagesDriver, aws_ecr_driver: AwsEcrDriver):
    monkeypatch = MonkeyPatch()
    joinery = Joinery(Ontology())
    monkeypatch.setattr(joinery, "local_images", local_images_driver)
    monkeypatch.setattr(joinery, "ecr_images", aws_ecr_driver)
    return joinery
