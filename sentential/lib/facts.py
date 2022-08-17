from os import getenv
import re
import typer
import boto3
from sentential.lib.clients import clients
from sentential.lib.shapes.internal import derive_paths


def lazy_property(fn):
    """Decorator that makes a property lazy-evaluated."""
    attr_name = "_lazy_" + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazy_property


class Facts:
    """Most properties in this object are lazy loaded, don't get the data if the data isn't needed"""

    def __init__(
        self,
        runtime: str = None,
    ) -> None:
        self.runtime = runtime

    @lazy_property
    def repository_name(self):
        try:
            repo = None
            with open("./Dockerfile") as file:
                for line in file.readlines():
                    if "FROM runtime AS" in line:
                        repo = line.split("AS")[1].strip()
                if repo is not None:
                    print(f"found repo to be {repo}")
                    return repo
                else:
                    print("Dockerfile not formed for sentential")
                    raise typer.Exit(code=1)
        except IOError:
            print("no Dockerfile present, run `sntl init` first")
            raise typer.Exit(code=1)


    @lazy_property
    def kms_key_alias(self):
        return getenv("AWS_KMS_KEY_ALIAS", default="aws/ssm")

    @lazy_property
    def partition(self):
        # TODO: when we replace chamber in the image, stop doing this .lower() nonsense
        return getenv(
            "PARTITION", default=clients.sts.get_caller_identity().get("UserId")
        ).lower()

    @lazy_property
    def region(self):
        return boto3.session.Session().region_name

    @lazy_property
    def path(self):
        return derive_paths()

    @lazy_property
    def account_id(self):
        return clients.sts.get_caller_identity().get("Account")

    @lazy_property
    def kms_key_id(self):
        return [
            ssm_key["TargetKeyId"]
            for ssm_key in boto3.client("kms").list_aliases()["Aliases"]
            if self.kms_key_alias in ssm_key["AliasName"]
        ][0]

    @lazy_property
    def repository_url(self):
        return f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{self.repository_name}"

    @lazy_property
    def registry_url(self):
        return f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com"


class Factual:
    def __init__(self) -> None:
        self.facts = Facts()
