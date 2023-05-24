from os.path import exists
from os import getcwd
import json
from sentential.lib.exceptions import SntlException
from sentential.lib.clients import clients


class Assurances:
    @classmethod
    def build(cls) -> None:
        cls._dockerfile_present()
        cls._dockerfile_valid()

    @classmethod
    def render(cls) -> None:
        cls._policy_present()
        cls._policy_valid()

    @classmethod
    def deploy(cls) -> None:
        cls._policy_present()
        cls._policy_valid()
        # cls._aws_authenticated() # slow

    @classmethod
    def _dockerfile_present(cls) -> None:
        if not exists(f"{getcwd()}/Dockerfile"):
            raise SntlException("Dockerfile not present present")

    @classmethod
    def _dockerfile_valid(cls) -> None:
        repo = None
        with open("./Dockerfile") as file:
            for line in file.readlines():
                if "FROM runtime AS" in line:
                    repo = line.split("AS")[1].strip()
        if repo is None:
            raise SntlException("Dockerfile not formed for sentential")

    @classmethod
    def _policy_present(cls) -> None:
        if not exists(f"{getcwd()}/policy.json"):
            raise SntlException("policy.json not present")

    @classmethod
    def _policy_valid(cls) -> None:
        try:
            json.loads(open(f"{getcwd()}/policy.json").read())
        except json.decoder.JSONDecodeError:
            raise SntlException("policy.json is not valid json")

    @classmethod
    def _aws_authenticated(cls):
        clients.sts.get_caller_identity()
