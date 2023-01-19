import os
from time import sleep
from typing import Dict, List, Optional, Union, cast
from sentential.lib.drivers.spec import LambdaDriver
from sentential.lib.ontology import Ontology
from sentential.lib.exceptions import AwsDriverError
from sentential.lib.shapes import (
    LAMBDA_ROLE_POLICY_JSON,
    Architecture,
    AwsImageDetail,
    AwsManifestList,
    LambdaInvokeResponse,
    Provision,
    AwsManifestListDistribution,
)
from sentential.lib.clients import clients
from sentential.lib.template import Policy


class AwsLambdaDriver(LambdaDriver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.function_name = ontology.context.resource_name
        self.policy_arn = f"arn:aws:iam::{self.ontology.context.account_id}:policy/{self.ontology.context.resource_name}"

    @property
    def provision(self) -> Provision:
        # there must be a better way to do polymorphic type stuff...
        return cast(Provision, self.ontology.configs.parameters)

    def deploy(self, image: AwsImageDetail, arch: Union[Architecture, None]) -> str:
        chosen_dist = self._choose_dist(image, arch)

        self.ontology.envs.export_defaults()
        self.ontology.tags.export_defaults()

        tags = self.ontology.tags.as_dict()

        clients.iam.attach_role_policy(
            RoleName=self._put_role(tags)["Role"]["RoleName"],
            PolicyArn=self._put_policy(tags)["Policy"]["Arn"],
        )
        self._put_lambda(chosen_dist, tags)

        return f"deployed {self.ontology.context.resource_name} to aws"

    def _choose_dist(
        self, image: AwsImageDetail, arch: Union[Architecture, None]
    ) -> AwsManifestListDistribution:
        if not isinstance(image.imageManifest, AwsManifestList):
            raise AwsDriverError(f"image manifest not of type manifest list")

        chosen_dist = None
        archs = [
            manifest.platform.architecture for manifest in image.imageManifest.manifests
        ]

        if len(image.imageManifest.manifests) == 0:
            raise AwsDriverError(f"image manifest list is empty")

        if arch is None and len(image.imageManifest.manifests) == 1:
            return image.imageManifest.manifests[0]
        if arch is None and len(image.imageManifest.manifests) > 1:
            raise AwsDriverError(f"must specify an architecture {archs}")
        else:
            for choice in image.imageManifest.manifests:
                if choice.platform.architecture == arch.value:
                    chosen_dist = choice

        if chosen_dist is None:
            raise AwsDriverError(
                f"no such distribution for {arch} found in image manifest list\n available: {archs}"
            )

        return chosen_dist

    def destroy(self) -> None:
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
                PolicyArn=self.policy_arn, RoleName=self.function_name
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
            clients.iam.delete_role(RoleName=self.function_name)
        except clients.iam.exceptions.NoSuchEntityException:
            pass

    def logs(self, follow: bool = False) -> None:
        cmd = ["aws", "logs", "tail", f"/aws/lambda/{self.function_name}"]
        if follow:
            cmd.append("--follow")
        os.system(" ".join(cmd))

    def invoke(self, payload: str) -> str:
        response = clients.lmb.invoke(
            FunctionName=self.function_name, Payload=payload, LogType="Tail"
        )
        response["Payload"] = response["Payload"].read()
        response["Payload"] = response["Payload"].decode("utf-8")
        return LambdaInvokeResponse(**response).json()

    def _put_role(self, tags: Optional[Dict[str, str]] = None) -> Dict:
        role_name = self.function_name
        try:
            clients.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=LAMBDA_ROLE_POLICY_JSON,
            )

            clients.iam.get_waiter("role_exists").wait(RoleName=role_name)

        except clients.iam.exceptions.EntityAlreadyExistsException:
            clients.iam.update_assume_role_policy(
                RoleName=role_name,
                PolicyDocument=LAMBDA_ROLE_POLICY_JSON,
            )

        clients.iam.get_waiter("role_exists").wait(RoleName=role_name)

        if tags:
            clients.iam.tag_role(
                RoleName=role_name,
                Tags=[{"Key": key, "Value": value} for (key, value) in tags.items()],
            )

        return clients.iam.get_role(RoleName=role_name)

    def _put_policy(self, tags: Optional[Dict[str, str]] = None) -> Dict:
        policy_json = Policy(self.ontology).render()
        policy_name = self.function_name
        policy_arn = self.policy_arn

        try:
            policy = clients.iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=policy_json,
            )

        except clients.iam.exceptions.EntityAlreadyExistsException:
            policy = clients.iam.get_policy(PolicyArn=policy_arn)

            versions = clients.iam.list_policy_versions(PolicyArn=policy_arn)[
                "Versions"
            ]

            if len(versions) >= 5:
                clients.iam.delete_policy_version(
                    PolicyArn=policy_arn, VersionId=versions[-1]["VersionId"]
                )

            clients.iam.create_policy_version(
                PolicyArn=policy_arn,
                PolicyDocument=policy_json,
                SetAsDefault=True,
            )

        if tags:
            clients.iam.tag_policy(
                PolicyArn=policy_arn,
                Tags=[{"Key": key, "Value": value} for (key, value) in tags.items()],
            )

        clients.iam.get_waiter("policy_exists").wait(PolicyArn=policy_arn)
        return policy

    def _put_lambda(
        self, image: AwsManifestListDistribution, tags: Optional[Dict[str, str]] = None
    ) -> Dict:
        role_name = self.function_name
        function_name = self.function_name
        role_arn = clients.iam.get_role(RoleName=role_name)["Role"]["Arn"]
        image_arch = (
            "x86_64"
            if image.platform.architecture == "amd64"
            else image.platform.architecture
        )
        image_uri = f"{self.ontology.context.repository_url}@{image.digest}"
        envs_path = self.ontology.envs.path

        sleep(10)
        try:
            function = clients.lmb.create_function(
                FunctionName=function_name,
                Role=role_arn,
                PackageType="Image",
                Code={"ImageUri": image_uri},
                Description=f"sententially deployed {image_uri}",
                Environment={"Variables": {"PARTITION": envs_path}},
                Architectures=[image_arch],
                EphemeralStorage={"Size": self.provision.storage},
                MemorySize=self.provision.memory,
                Timeout=self.provision.timeout,
                VpcConfig={
                    "SubnetIds": self.provision.subnet_ids,
                    "SecurityGroupIds": self.provision.security_group_ids,
                },
            )

        except clients.lmb.exceptions.ResourceConflictException:
            function = clients.lmb.update_function_configuration(
                FunctionName=function_name,
                Role=role_arn,
                Description=f"sententially deployed {image_uri}",
                Environment={"Variables": {"PARTITION": envs_path}},
                EphemeralStorage={"Size": self.provision.storage},
                MemorySize=self.provision.memory,
                Timeout=self.provision.timeout,
                VpcConfig={
                    "SubnetIds": self.provision.subnet_ids,
                    "SecurityGroupIds": self.provision.security_group_ids,
                },
            )

            clients.lmb.get_waiter("function_updated_v2").wait(
                FunctionName=function_name
            )

            clients.lmb.update_function_code(
                FunctionName=function_name,
                ImageUri=image_uri,
                Architectures=[image_arch],
                Publish=True,
            )

        if tags:
            clients.lmb.tag_resource(Resource=function["FunctionArn"], Tags=tags)

        return function
