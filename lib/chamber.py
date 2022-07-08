from shutil import which
from os import environ
from lib.config import Config
from subprocess import run as shell

class ChamberWrapper:
    def __init__(self, repository_name: str):
        self.config = Config(repository_name=repository_name)
        if which("chamber") is None:
            raise SystemExit("please install chamber")
        environ["CHAMBER_KMS_KEY_ALIAS"] = self.config.kms_key_alias

    def write(self, key, value):
        shell(["chamber", "write", self.config.repository_name, key, value])

    def read(self, key=None):
        if key is None:
            shell(["chamber", "list", self.config.repository_name])
        else:
            shell(["chamber", "read", self.config.repository_name, key])

    def delete(self, key):
        shell(["chamber", "delete", self.config.repository_name, key])