from functools import lru_cache
import json
from time import sleep
from typing import List
from sentential.lib.clients import clients
from sentential.lib.shapes.aws import LAMBDA_ROLE_POLICY_JSON, AWSPolicyDocument
from sentential.lib.shapes.internal import Spec
from sentential.lib.facts import facts
from jinja2 import Template
from IPython import embed
from sentential.lib.store import ConfigStore


class Image:
    def __init__(self, tag: str = "latest") -> None:
        self.repository_name = facts.repository_name
        self.tag = tag

    def spec(self) -> Spec:
        metadata = self._fetch_metadata()
        spec_data = json.loads(metadata["config"]["Labels"]["spec"])
        return Spec(**spec_data)

    def arch(self) -> str:
        metadata = self._fetch_metadata()
        if metadata["architecture"] == "amd64":
            return "x86_64"
        else:
            return metadata["architecture"]

    @lru_cache(maxsize=1)
    def _fetch_metadata(self) -> dict:
        image = clients.ecr.batch_get_image(
            repositoryName=facts.repository_name,
            imageIds=[{"imageTag": self.tag}],
            acceptedMediaTypes=["application/vnd.docker.distribution.manifest.v1+json"],
        )["images"][0]
        image_manifest = json.loads(image["imageManifest"])
        metadata = image_manifest["history"][0]["v1Compatibility"]
        return json.loads(metadata)


class Lambda:
    def __init__(self, image: Image) -> None:
        self.image = image
        self.policy_arn = (
            f"arn:aws:iam::{facts.account_id}:policy/{self.image.spec().policy_name}"
        )

    def deploy(self):
        clients.iam.attach_role_policy(
            RoleName=self._put_role()["Role"]["RoleName"],
            PolicyArn=self._put_policy()["Policy"]["Arn"],
        )
        self._put_lambda()
        print(self._put_url())

    def destroy(self):
        try:
            clients.lmb.delete_function_url_config(
                FunctionName=self.image.repository_name
            )
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass

        try:
            clients.lmb.delete_function(FunctionName=self.image.repository_name)
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass

        try:
            clients.iam.detach_role_policy(
                PolicyArn=self.policy_arn, RoleName=self.image.spec().role_name
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
            clients.iam.delete_role(RoleName=self.image.spec().role_name)
        except clients.iam.exceptions.NoSuchEntityException:
            pass

    def _put_role(self) -> object:
        try:
            role = clients.iam.create_role(
                RoleName=self.image.spec().role_name,
                AssumeRolePolicyDocument=LAMBDA_ROLE_POLICY_JSON,
            )

            clients.iam.get_waiter("role_exists").wait(
                RoleName=self.image.spec().role_name
            )

        except clients.iam.exceptions.EntityAlreadyExistsException:
            role = clients.iam.get_role(RoleName=self.image.spec().role_name)

            clients.iam.update_assume_role_policy(
                RoleName=self.image.spec().role_name,
                PolicyDocument=LAMBDA_ROLE_POLICY_JSON,
            )

        clients.iam.get_waiter("role_exists").wait(RoleName=self.image.spec().role_name)

        return role

    def _put_policy(self) -> object:
        policy_json = Template(self.image.spec().policy.json(exclude_none=True)).render(
            facts=facts, config=ConfigStore().parameters()
        )
        try:
            policy = clients.iam.create_policy(
                PolicyName=self.image.spec().policy_name, PolicyDocument=policy_json
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

        clients.iam.get_waiter("policy_exists").wait(PolicyArn=self.policy_arn)
        return policy

    def _put_url(self) -> object:
        config = {
            "FunctionName": self.image.repository_name,
            "AuthType": "NONE",
            "Cors": {
                "AllowHeaders": ["*"],
                "AllowMethods": ["*"],
                "AllowOrigins": ["*"],
                "ExposeHeaders": ["*"],
            },
        }

        try:
            clients.lmb.create_function_url_config(**config)
        except clients.lmb.exceptions.ResourceConflictException:
            clients.lmb.update_function_url_config(**config)

        return clients.lmb.get_function_url_config(
            FunctionName=self.image.repository_name
        )

    def _put_lambda(self):
        role_arn = clients.iam.get_role(RoleName=self.image.spec().role_name)["Role"][
            "Arn"
        ]
        image_uri = f"{facts.repository_url}:{self.image.tag}"
        sleep(10)
        try:
            function = clients.lmb.create_function(
                FunctionName=self.image.repository_name,
                Role=role_arn,
                PackageType="Image",
                Code={"ImageUri": image_uri},
                Description=f"sententially deployed {self.image.repository_name}:{self.image.tag}",
                Environment={"Variables": {"PREFIX": self.image.repository_name}},
                Architectures=[self.image.arch()],
            )

            clients.lmb.add_permission(
                FunctionName=self.image.repository_name,
                StatementId="FunctionURLAllowPublicAccess",
                Action="lambda:InvokeFunctionUrl",
                Principal="*",
                FunctionUrlAuthType="NONE",
            )

            return function
        except clients.lmb.exceptions.ResourceConflictException:
            function = clients.lmb.update_function_configuration(
                FunctionName=self.image.repository_name,
                Role=role_arn,
                Description=f"sententially deployed {self.image.repository_name}:{self.image.tag}",
                Environment={"Variables": {"PREFIX": self.image.repository_name}},
            )

            clients.lmb.get_waiter("function_updated_v2").wait(
                FunctionName=self.image.repository_name
            )

            clients.lmb.update_function_code(
                FunctionName=self.image.repository_name,
                ImageUri=image_uri,
                Publish=True,
            )

            try:
                clients.lmb.remove_permission(
                    FunctionName=self.image.repository_name,
                    StatementId="FunctionURLAllowPublicAccess",
                )
            except clients.lmb.exceptions.ResourceNotFoundException:
                pass

            clients.lmb.add_permission(
                FunctionName=self.image.repository_name,
                StatementId="FunctionURLAllowPublicAccess",
                Action="lambda:InvokeFunctionUrl",
                Principal="*",
                FunctionUrlAuthType="NONE",
            )

            return function


class Repository:
    def __init__(self) -> None:
        pass

    def images(self) -> List[Image]:
        images = clients.ecr.describe_images(repositoryName=facts.repository_name)[
            "imageDetails"
        ]
        filtered = []
        for image in images:
            if "imageTags" in image:
                for tag in image["imageTags"]:
                    filtered.append(Image(tag))
        return filtered
