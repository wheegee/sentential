import json
import os
from time import sleep
from typing import Dict, List, Optional, cast
from sentential.lib.exceptions import AwsDriverError
from sentential.lib.drivers.spec import LambdaDriver
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.shapes import (
    LAMBDA_ROLE_POLICY_JSON,
    Image,
    LambdaInvokeResponse,
    Provision,
)
from sentential.lib.clients import clients
from sentential.lib.template import Policy

#
# NOTE: Docker images in ECR are primary key'd (conceptually) off of their digest, this is normalized by the Image type
#


class AwsLambdaDriver(LambdaDriver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.function_name = ontology.context.resource_name
        self.policy_arn = f"arn:aws:iam::{self.ontology.context.account_id}:policy/{self.ontology.context.resource_name}"

    @property
    def provision(self) -> Provision:
        # there must be a better way to do polymorphic type stuff...
        return cast(Provision, self.ontology.configs.parameters)

    def deploy(self, image: Image) -> Image:
        self.ontology.envs.export_defaults()
        clients.iam.attach_role_policy(
            RoleName=self._put_role()["Role"]["RoleName"],
            PolicyArn=self._put_policy()["Policy"]["Arn"],
        )
        self._put_lambda(image)
        return image

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

    def invoke(self, payload: str) -> LambdaInvokeResponse:
        response = clients.lmb.invoke(
            FunctionName=self.function_name, Payload=payload, LogType="Tail"
        )
        response["Payload"] = response["Payload"].read()
        response["Payload"] = response["Payload"].decode("utf-8")
        return LambdaInvokeResponse(**response)

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
                PolicyName=policy.name,
                Tags=[{"Key": key, "Value": value} for (key, value) in tags.items()],
            )

        clients.iam.get_waiter("policy_exists").wait(PolicyArn=policy_arn)
        return policy

    def _put_lambda(self, image: Image, tags: Optional[Dict[str, str]] = None) -> Dict:
        role_name = self.function_name
        function_name = self.function_name
        role_arn = clients.iam.get_role(RoleName=role_name)["Role"]["Arn"]
        image_arch = "x86_64" if image.arch == "amd64" else image.arch
        envs_path = self.ontology.envs.path
        sleep(10)
        try:
            function = clients.lmb.create_function(
                FunctionName=function_name,
                Role=role_arn,
                PackageType="Image",
                Code={"ImageUri": image.uri},
                Description=f"sententially deployed {image.uri}",
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

            return function
        except clients.lmb.exceptions.ResourceConflictException:
            function = clients.lmb.update_function_configuration(
                FunctionName=function_name,
                Role=role_arn,
                Description=f"sententially deployed {image.uri}",
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
                ImageUri=image.uri,
                Architectures=[image_arch],
                Publish=True,
            )

            if tags:
                clients.lmb.tag_resource(Resource=function.arn, Tags=tags)

            return function
