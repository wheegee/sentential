import boto3
from os import getenv, environ
from sentential.lib.exceptions import ContextError
from sentential.lib.clients import clients
from sentential.lib.shapes import derive_paths, Paths, AWSCallerIdentity
from sentential.lib.exceptions import SntlException


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
    def resource_name(self) -> str:
        return f"{self.partition}-{self.region}-{self.repository_name}"

    @property
    def kms_key_alias(self) -> str:
        return getenv("AWS_KMS_KEY_ALIAS", default="aws/ssm")

    @property  # TODO: make this a cached property
    def caller_identity(self) -> AWSCallerIdentity:
        response = clients.sts.get_caller_identity()
        return AWSCallerIdentity(**response)

    @property
    def partition(self) -> str:
        if "PARTITION" in environ:
            return str(getenv("PARTITION"))
        else:
            user_id = self.caller_identity.UserId
            if ":" in user_id:
                # The ID before ':' in an assumed role seems to remain constant... time will tell.
                return str(user_id.split(":")[0])
            else:
                return user_id

    @property
    def region(self) -> str:
        return str(boto3.Session().region_name)

    @property
    def path(self) -> Paths:
        return derive_paths()

    @property
    def account_id(self) -> str:
        return self.caller_identity.Account

    @property
    def kms_key_id(self) -> str:
        try:
            return [
                ssm_key["TargetKeyId"]
                for ssm_key in clients.kms.list_aliases()["Aliases"]
                if self.kms_key_alias in ssm_key["AliasName"]
            ][0]
        except IndexError:
            raise ContextError("Key specified by AWS_KMS_KEY_ALIAS does not exist")
        except KeyError:
            raise ContextError(
                "If region has not yet written an ssm parameter with the default key, the default kms key will not yet exist \\o/."
            )

    @property
    def repository_url(self) -> str:
        return f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{self.repository_name}"

    @property
    def ecr_rest_url(self) -> str:
        return f"https://{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/v2/{self.repository_name}"

    @property
    def registry_url(self) -> str:
        return f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com"
