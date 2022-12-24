import pytest

@pytest.mark.usefixtures("moto", "init", "invoke")
class TestRoot:
    def test_build(self, invoke):
        result = invoke(["build"])
        assert result.exit_code == 0

    # def test_ls(self, invoke):
    #     from IPython import embed
    #     embed()