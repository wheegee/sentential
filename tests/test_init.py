from os.path import exists
from tests.helper import *
import in_place
from shutil import copyfile
from IPython import embed
from sentential.sntl import root as sntl


def test_init():
    result = runner.invoke(sntl, ["init", "test", "python"])
    assert result.exit_code == 0


def test_files_exist():
    for file in [
        "Dockerfile",
        "policy.json",
        ".sntl/sentential.yml",
        ".sntl/wrapper.sh",
    ]:
        assert exists(file)


def test_build():
    copyfile(f"{project}/tests/fixtures/app.py", f"{repo.name}/src/app.py")
    copyfile(
        f"{project}/tests/fixtures/requirements.txt",
        f"{repo.name}/src/requirements.txt",
    )
    with in_place.InPlace(f"{repo.name}/Dockerfile") as fp:
        for line in fp:
            if "# insert application specific build steps here" in line:
                fp.write("RUN pip install -r requirements.txt\n")
            else:
                fp.write(line)

    result = runner.invoke(sntl, ["build"])
    assert result.exit_code == 0
