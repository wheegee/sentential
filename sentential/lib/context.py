import boto3
from os import getenv
from sentential.lib.exceptions import ContextError
from sentential.lib.clients import clients
from sentential.lib.shapes import derive_paths, Paths


class Context:
    @property
    def repository_name(self) -> str:
        try:
            repo = None
            with open("./Dockerfile") as file:
                for line in file.readlines():
                    if "FROM runtime AS" in line:
                        repo = line.split("AS")[1].strip()
                if repo is not None:
                    return repo
                else:
                    raise ContextError("Dockerfile not formed for sentential")
        except IOError:
            raise ContextError("no Dockerfile present, run `sntl init` first")

    @property
    def kms_key_alias(self) -> str:
        return getenv("AWS_KMS_KEY_ALIAS", default="aws/ssm")

    @property
    def partition(self) -> str:
        return getenv(
            "PARTITION", default=clients.sts.get_caller_identity().get("UserId")
        )

    @property
    def region(self) -> str:
        return str(boto3.Session().region_name)

    @property
    def path(self) -> Paths:
        return derive_paths()

    @property
    def account_id(self) -> str:
        return clients.sts.get_caller_identity().get("Account")

    @property
    def kms_key_id(self) -> str:
        # TODO: if region has not yet written an ssm param with the default key, the kms key will not yet exist \o/
        return [
            ssm_key["TargetKeyId"]
            for ssm_key in boto3.client("kms").list_aliases()["Aliases"]
            if self.kms_key_alias in ssm_key["AliasName"]
        ][0]

    @property
    def repository_url(self) -> str:
        return f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{self.repository_name}"

    @property
    def registry_url(self) -> str:
        return f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com"
