from sentential.sntl import root
from os.path import exists
from tests.helper import *

def test_init():
    result = runner.invoke(root, ["init", "test", "ruby"])
    assert result.exit_code == 0

def test_files_exist():
    for file in ["Dockerfile", "policy.json", ".sntl/sentential.yml", ".sntl/wrapper.sh"]:
        assert exists(file)
