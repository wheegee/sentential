from typing import List
import pytest
from sentential.lib.joinery import Joinery
from tests.helpers import table_body

@pytest.mark.usefixtures("moto", "init", "mock_repo", "cwi")
class TestJoinery:
    id_index = 0
    digest_index = 1
    uri_index = 2
    tags_index = 3
    arch_index = 4
    version_index = 5

    #
    # Test Helpers
    #

    def get_versions(self, table) -> List[str]:
        versions = []
        for image in table:
            versions = list(set(versions + image[self.version_index]))
        return versions

    def get_images_by_version(self, table, version) -> List[List[str]]:
        images = []
        for image in table:
            if version in image[self.version_index]:
                images.append(image)
        return images

    #
    # Tests
    #

    def test_list(self, joinery: Joinery):
        table = table_body(joinery.list())
        versions = self.get_versions(table)
        for version in versions:
            images = self.get_images_by_version(table, version)
            assert len(images) == 2 or len(images) == 1
            if len(images) == 2:
                assert images[0][self.id_index] != images[1][self.id_index]
                assert images[0][self.digest_index] == images[1][self.digest_index]
                assert images[0][self.uri_index] != images[1][self.uri_index]
                assert images[0][self.arch_index] != images[1][self.arch_index]
                assert images[0][self.version_index] == images[1][self.version_index]
            if len(images) == 1:
                # implement tests for single arch cases
                ...