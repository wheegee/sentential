from typing import Dict, List
import boto3
from os import getenv, environ
from sentential.lib.exceptions import ContextError
from sentential.lib.clients import clients
from sentential.lib.shapes import derive_paths, Paths, AWSCallerIdentity


class Context:
    def dict(self) -> Dict:
        all = {}
        for method in dir(self):
            if "__" not in method:
                all[method] = getattr(self, method)
        return all

    @property
    def repository_name(self) -> str:
        with open("./Dockerfile") as file:
            for line in file.readlines():
                if "FROM runtime AS" in line:
                    return line.split("AS")[1].strip()
        raise ContextError("No runtime stage found in Dockerfile")

    @property
    def resource_name(self) -> str:
        return f"{self.partition}-{self.repository_name}"

    @property
    def resource_arn(self) -> str:
        return f"arn:aws:lambda:{self.region}:{self.account_id}:function:{self.resource_name}"

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
