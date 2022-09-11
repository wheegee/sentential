from functools import lru_cache
import os
import json
import re
from time import sleep
from typing import List
from jinja2 import Template
from distutils.version import LooseVersion
from sentential.lib.clients import clients
from sentential.lib.const import SEMVER_REGEX
from sentential.lib.shapes.aws import LAMBDA_ROLE_POLICY_JSON
from sentential.lib.facts import Factual, Facts, lazy_property
from sentential.lib.store import Env, Provision, Tag


class Image(Factual):
    def __init__(self, tag: str = "latest") -> None:
        super().__init__()
        self.tag = tag

    @lazy_property
    def id(self) -> str:
        return self.metadata["imageId"]

    @lazy_property
    def arch(self) -> str:
        if self.metadata["architecture"] == "amd64":
            return "x86_64"
        else:
            return self.metadata["architecture"]

    @lazy_property
    def metadata(self) -> dict:
        image = clients.ecr.batch_get_image(
            repositoryName=self.facts.repository_name,
            imageIds=[{"imageTag": self.tag}],
            acceptedMediaTypes=["application/vnd.docker.distribution.manifest.v1+json"],
        )["images"][0]
        image_manifest = json.loads(image["imageManifest"])
        metadata = json.loads(image_manifest["history"][0]["v1Compatibility"])
        metadata["repositoryName"] = image["repositoryName"]
        metadata["imageId"] = image["imageId"]["imageDigest"]
        return metadata


class Lambda(Factual):
    def __init__(self, image: Image) -> None:
        super().__init__()
        self.image = image
        self.partition = self.facts.partition
        self.image_uri = f"{self.facts.repository_url}:{self.image.tag}"
        self.function_name = (
            f"{self.partition}-{self.facts.region}-{self.facts.repository_name}"
        )
        self.role_name = (
            f"{self.partition}-{self.facts.region}-{self.facts.repository_name}"
        )
        self.policy_name = (
            f"{self.partition}-{self.facts.region}-{self.facts.repository_name}"
        )
        self.policy_arn = (
            f"arn:aws:iam::{self.facts.account_id}:policy/{self.policy_name}"
        )
        self.env = Env()
        self.provision = Provision().parameters()
        self.tags = Tag().as_dict()

    @classmethod
    def deployed(cls):
        facts = Facts()
        function_name = f"{facts.partition}-{facts.region}-{facts.repository_name}"
        try:
            lmb = clients.lmb.get_function(FunctionName=function_name)
            tag = lmb["Code"]["ImageUri"].split("/")[1].split(":")[1]
            return cls(Image(tag))
        except clients.lmb.exceptions.ResourceNotFoundException:
            return None

    def deploy(self, public_url: bool):
        clients.iam.attach_role_policy(
            RoleName=self._put_role()["Role"]["RoleName"],
            PolicyArn=self._put_policy()["Policy"]["Arn"],
        )

        function = self._put_lambda()

        if public_url:
            print(self._put_url()["FunctionUrl"])
        else:
            print(function["FunctionArn"])

    def destroy(self):
        try:
            clients.lmb.delete_function_url_config(FunctionName=self.function_name)
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass

        try:
            clients.lmb.delete_function(FunctionName=self.function_name)
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass

        try:
            clients.iam.detach_role_policy(
                PolicyArn=self.policy_arn, RoleName=self.role_name
            )

            policy_versions = clients.iam.list_policy_versions(
                PolicyArn=self.policy_arn
            )["Versions"]
            for policy_version in policy_versions:
                if not policy_version["IsDefaultVersion"]:
                    clients.iam.delete_policy_version(
                        PolicyArn=self.policy_arn, VersionId=policy_version["VersionId"]
                    )

            clients.iam.delete_policy(PolicyArn=self.policy_arn)
        except clients.iam.exceptions.NoSuchEntityException:
            pass

        try:
            clients.iam.delete_role(RoleName=self.role_name)
        except clients.iam.exceptions.NoSuchEntityException:
            pass

    def _put_role(self) -> object:
        try:
            clients.iam.create_role(
                RoleName=self.role_name,
                AssumeRolePolicyDocument=LAMBDA_ROLE_POLICY_JSON,
            )

            clients.iam.get_waiter("role_exists").wait(RoleName=self.role_name)

        except clients.iam.exceptions.EntityAlreadyExistsException:
            clients.iam.update_assume_role_policy(
                RoleName=self.role_name,
                PolicyDocument=LAMBDA_ROLE_POLICY_JSON,
            )

        clients.iam.get_waiter("role_exists").wait(RoleName=self.role_name)

        if self.tags:
            clients.iam.tag_role(
                RoleName=self.role_name,
                Tags=[
                    {"Key": key, "Value": value} for (key, value) in self.tags.items()
                ],
            )

        return clients.iam.get_role(RoleName=self.role_name)

    def _put_policy(self) -> object:
        policy_json = Template(self.facts.path.policy.read_text()).render(
            facts=self.facts,
            env=self.env.parameters(),
        )
        try:
            policy = clients.iam.create_policy(
                PolicyName=self.policy_name,
                PolicyDocument=policy_json,
            )

        except clients.iam.exceptions.EntityAlreadyExistsException:
            policy = clients.iam.get_policy(PolicyArn=self.policy_arn)

            versions = clients.iam.list_policy_versions(PolicyArn=self.policy_arn)[
                "Versions"
            ]

            if len(versions) >= 5:
                clients.iam.delete_policy_version(
                    PolicyArn=self.policy_arn, VersionId=versions[-1]["VersionId"]
                )

            clients.iam.create_policy_version(
                PolicyArn=self.policy_arn,
                PolicyDocument=policy_json,
                SetAsDefault=True,
            )

        if self.tags:
            clients.iam.tag_policy(
                PolicyName=policy.name,
                Tags=[
                    {"Key": key, "Value": value} for (key, value) in self.tags.items()
                ],
            )

        clients.iam.get_waiter("policy_exists").wait(PolicyArn=self.policy_arn)
        return policy

    def _put_url(self) -> object:
        config = {
            "FunctionName": self.function_name,
            "AuthType": self.provision.auth_type,
            "Cors": {
                "AllowHeaders": self.provision.allow_headers,
                "AllowMethods": self.provision.allow_methods,
                "AllowOrigins": self.provision.allow_origins,
                "ExposeHeaders": self.provision.expose_headers,
            },
        }

        try:
            clients.lmb.create_function_url_config(**config)
        except clients.lmb.exceptions.ResourceConflictException:
            clients.lmb.update_function_url_config(**config)

        return clients.lmb.get_function_url_config(FunctionName=self.function_name)

    def _put_lambda(self):
        role_arn = clients.iam.get_role(RoleName=self.role_name)["Role"]["Arn"]
        sleep(10)
        try:
            function = clients.lmb.create_function(
                FunctionName=self.function_name,
                Role=role_arn,
                PackageType="Image",
                Code={"ImageUri": self.image_uri},
                Description=f"sententially deployed {self.facts.repository_name}:{self.image.tag}",
                Environment={"Variables": {"PARTITION": self.env.path}},
                Architectures=[self.image.arch],
                EphemeralStorage={"Size": self.provision.storage},
                MemorySize=self.provision.memory,
                Timeout=self.provision.timeout,
                VpcConfig={
                    "SubnetIds": self.provision.subnet_ids,
                    "SecurityGroupIds": self.provision.security_group_ids,
                },
            )

            clients.lmb.add_permission(
                FunctionName=self.function_name,
                StatementId="FunctionURLAllowPublicAccess",
                Action="lambda:InvokeFunctionUrl",
                Principal="*",
                FunctionUrlAuthType="NONE",
            )

            return function
        except clients.lmb.exceptions.ResourceConflictException:
            function = clients.lmb.update_function_configuration(
                FunctionName=self.function_name,
                Role=role_arn,
                Description=f"sententially deployed {self.facts.repository_name}:{self.image.tag}",
                Environment={"Variables": {"PARTITION": self.env.path}},
                EphemeralStorage={"Size": self.provision.storage},
                MemorySize=self.provision.memory,
                Timeout=self.provision.timeout,
                VpcConfig={
                    "SubnetIds": self.provision.subnet_ids,
                    "SecurityGroupIds": self.provision.security_group_ids,
                },
            )

            clients.lmb.get_waiter("function_updated_v2").wait(
                FunctionName=self.function_name
            )

            clients.lmb.update_function_code(
                FunctionName=self.function_name,
                ImageUri=self.image_uri,
                Publish=True,
            )

            try:
                clients.lmb.remove_permission(
                    FunctionName=self.function_name,
                    StatementId="FunctionURLAllowPublicAccess",
                )
            except clients.lmb.exceptions.ResourceNotFoundException:
                pass

            clients.lmb.add_permission(
                FunctionName=self.function_name,
                StatementId="FunctionURLAllowPublicAccess",
                Action="lambda:InvokeFunctionUrl",
                Principal="*",
                FunctionUrlAuthType="NONE",
            )

            if self.tags:
                clients.lmb.tag_resource(Resource=function.arn, Tags=self.tags)

            return function

    def logs(self, follow: bool = False):
        cmd = ["aws", "logs", "tail", f"/aws/lambda/{self.function_name}"]
        if follow:
            cmd.append("--follow")
        os.system(" ".join(cmd))


class Repository(Factual):
    def __init__(self) -> None:
        super().__init__()
        pass

    def images(self) -> List[Image]:
        images = clients.ecr.describe_images(repositoryName=self.facts.repository_name)[
            "imageDetails"
        ]
        filtered = []
        for image in images:
            if "imageTags" in image:
                for tag in image["imageTags"]:
                    # TODO: performance => let image be prepopulated with metadata at init, do bulk request here
                    filtered.append(Image(tag))
        return filtered

    def semver(self) -> List[Image]:
        matcher = re.compile(SEMVER_REGEX)
        images = [image for image in self.images() if matcher.match(image.tag)]
        images.sort(key=lambda image: LooseVersion(image.tag))
        return images

    def latest(self) -> Image:
        try:
            return self.semver()[-1]
        except IndexError:
            return None
