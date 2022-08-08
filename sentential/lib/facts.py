import re
import typer
import boto3
from enum import Enum
from sentential.lib.clients import clients
from sentential.lib.shapes.internal import SntlMeta, derive_paths

try:
    SNTL_FILE = SntlFile(**safe_load(open("./.sntl/sentential.yml")))
except:
    SNTL_FILE = SntlFile()


def dockerfile_meta():
    r = re.compile(r"^ENV\s([a-z].*)=(.*)", re.MULTILINE)
    try:
        with open("./Dockerfile") as file:
            dockerfile = file.read()
        meta = {match.group(1): match.group(2) for match in r.finditer(dockerfile)}
        return SntlMeta(**meta)
    except IOError:
        print("no Dockerfile present, run `sntl init` first")
        raise typer.Exit(code=1)


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
        kms_key_alias: str = "aws/ssm",
    ) -> None:
        self.runtime = runtime
        self.kms_key_alias = kms_key_alias

    @lazy_property
    def repository_name(self):
        return dockerfile_meta().repository_name

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
    def caller_id(self):
        return clients.sts.get_caller_identity().get("UserId")

    @lazy_property
    def kms_key_id(self):
        return [
            ssm_key["TargetKeyId"]
            for ssm_key in boto3.client("kms").list_aliases()["Aliases"]
            if self.kms_key_alias in ssm_key["AliasName"]
        ][0]

    @lazy_property
    def partitions(self):
        # TODO: reimplement partitions other than caller
        # partitions = {name: name for name in SNTL_META.partitions}
        partitions = {}
        partitions["default"] = self.caller_id.lower()
        return partitions

    @lazy_property
    def repository_url(self):
        return f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{self.repository_name}"

    @lazy_property
    def registry_url(self):
        return f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com"


class Factual:
    def __init__(self) -> None:
        self.facts = Facts()


# TODO: this will still work, but this init-at-bottom-of-file pattern is decidedly bad for testing. So remove it.
Partitions = Enum("Partitions", Facts().partitions)
