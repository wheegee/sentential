import boto3
from yaml import safe_load
from pathlib import Path
from sentential.lib.clients import clients
from sentential.lib.shapes.internal import Paths
from types import SimpleNamespace

SNTL_FILE = SimpleNamespace(**safe_load(open("./.sntl/sentential.yml")))

def lazy_property(fn):
    '''Decorator that makes a property lazy-evaluated.'''
    attr_name = '_lazy_' + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazy_property


class Facts:
    """Most properties in this object are lazy loaded, don't get the data if the data isn't needed"""
    def __init__(self, repository_name: str = SNTL_FILE.repository_name , runtime: str = None, kms_key_alias: str = "aws/ssm") -> None:
        self.repository_name = repository_name
        self.runtime = runtime
        self.kms_key_alias = kms_key_alias

    @lazy_property
    def region(self):
        print("this should not have happened")
        return boto3.session.Session().region_name
    
    @lazy_property
    def path(self):
        root = Path(".")
        return Paths(
            root=root,
            sntl=f"{root}/.sntl",
            src=Path(f"{root}/src"),
            sentential_file=Path(f"{root}/.sntl/sentential.yml"),
            dockerfile=Path(f"{root}/Dockerfile"),
            wrapper=Path(f"{root}/.sntl/wrapper.sh"),
            policy=Path(f"{root}/policy.json"),
        )

    @lazy_property
    def account_id(self):
        return clients.sts.get_caller_identity().get("Account")

    @lazy_property
    def kms_key_is(self):
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

facts = Facts()