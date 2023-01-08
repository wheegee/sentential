from typing import List
import pytest
from sentential.lib.joinery import Joinery
from tests.helpers import table_body


@pytest.mark.usefixtures("moto", "init", "mock_repo", "cwi")
class TestJoinery:
    #
    # Tests
    #

    def test_list(self, joinery: Joinery):
        table = table_body(joinery.list())
        assert len(table) > 0
        for row in table:
            assert "0.0" in row[0]
            assert "amd64, arm64" in row[1]
            assert row[2] is not None
