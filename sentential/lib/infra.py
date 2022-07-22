import json
from time import sleep
from sentential.lib.ecr import ECR
from sentential.lib.clients import clients
from sentential.lib.shapes.aws import ECREvent, AWSPolicyDocument, AWSPolicyStatement

LAMBDA_ROLE_POLICY = AWSPolicyDocument(
    Statement=[
        AWSPolicyStatement(
            Effect="Allow",
            Principal={"Service": "lambda.amazonaws.com"},
            Action="sts:AssumeRole",
        )
    ]
)


class Infra:
    def __init__(self, event: ECREvent) -> None:
        self.event = event
        self.registry_url = f"{event.account}.dkr.ecr.{event.region}.amazonaws.com"
        self.repository_url = f"{self.registry_url}/{event.detail.repository_name}"
        self.image_manifest = json.loads(
            clients.ecr.batch_get_image(
                repositoryName=event.detail.repository_name,
                imageIds=[{"imageTag": event.detail.image_tag}],
                acceptedMediaTypes=[
                    "application/vnd.docker.distribution.manifest.v1+json"
                ],
            )["images"][0]["imageManifest"]
        )
        self.spec = ECR(self.repository_url, event.detail.image_tag).fetch_spec()
        self.policy_arn = (
            f"arn:aws:iam::{self.event.account}:policy/{self.spec.policy_name}"
        )

    def _put_role(self):
        try:
            role = clients.iam.create_role(
                RoleName=self.spec.role_name,
                AssumeRolePolicyDocument=LAMBDA_ROLE_POLICY.json(exclude_none=True),
            )
            print("waiting for role to exist")
            clients.iam.get_waiter("role_exists").wait(RoleName=self.spec.role_name)
            return role
        except clients.iam.exceptions.EntityAlreadyExistsException:
            clients.iam.update_assume_role_policy(
                RoleName=self.spec.role_name,
                PolicyDocument=LAMBDA_ROLE_POLICY.json(exclude_none=True),
            )
            clients.iam.get_waiter("role_exists").wait(RoleName=self.spec.role_name)
            role = clients.iam.get_role(RoleName=self.spec.role_name)
            return role

    def _put_policy(self):
        try:
            policy = clients.iam.create_policy(
                PolicyName=self.spec.policy_name,
                PolicyDocument=self.spec.policy.json(exclude_none=True, by_alias=True),
            )
            print("waiting for policy to exist")
            clients.iam.get_waiter("policy_exists").wait(PolicyArn=self.policy_arn)
            return policy
        except clients.iam.exceptions.EntityAlreadyExistsException:
            versions = clients.iam.list_policy_versions(PolicyArn=self.policy_arn)[
                "Versions"
            ]
            if len(versions) >= 5:
                clients.iam.delete_policy_version(
                    PolicyArn=self.policy_arn, VersionId=versions[-1]["VersionId"]
                )

            clients.iam.create_policy_version(
                PolicyArn=self.policy_arn,
                PolicyDocument=self.spec.policy.json(exclude_none=True, by_alias=True),
                SetAsDefault=True,
            )
            clients.iam.get_waiter("policy_exists").wait(PolicyArn=self.policy_arn)
            return clients.iam.get_policy(PolicyArn=self.policy_arn)

    def _put_url(self):
        try:
            clients.lmb.create_function_url_config(
                FunctionName=self.event.detail.repository_name,
                AuthType="NONE",
                Cors={
                    "AllowHeaders": ["*"],
                    "AllowMethods": ["*"],
                    "AllowOrigins": ["*"],
                    "ExposeHeaders": ["*"],
                },
            )
        except clients.lmb.exceptions.ResourceConflictException:
            clients.lmb.update_function_url_config(
                FunctionName=self.event.detail.repository_name,
                AuthType="NONE",
                Cors={
                    "AllowHeaders": ["*"],
                    "AllowMethods": ["*"],
                    "AllowOrigins": ["*"],
                    "ExposeHeaders": ["*"],
                },
            )

        return clients.lmb.get_function_url_config(FunctionName=self.event.detail.repository_name)['FunctionUrl']

    def _configure_perms(self):
        role = self._put_role()
        policy = self._put_policy()
        clients.iam.attach_role_policy(
            RoleName=role["Role"]["RoleName"], PolicyArn=policy["Policy"]["Arn"]
        )

    def _configure_lambda(self):
        role_arn = clients.iam.get_role(RoleName=self.spec.role_name)["Role"]["Arn"]
        arch = None
        if self.image_manifest["architecture"] == "amd64":
            arch = "x86_64"
        else:
            arch = "arm64"
        sleep(10)
        try:
            function = clients.lmb.create_function(
                FunctionName=self.event.detail.repository_name,
                Role=role_arn,
                PackageType="Image",
                Code={
                    "ImageUri": f"{self.repository_url}:{self.event.detail.image_tag}"
                },
                Description=f"sententially deployed {self.event.detail.repository_name}:{self.event.detail.image_tag}",
                Environment={
                    "Variables": {"PREFIX": self.event.detail.repository_name}
                },
                Architectures=[arch],
            )

            clients.lmb.add_permission(
                FunctionName=self.event.detail.repository_name,
                StatementId="FunctionURLAllowPublicAccess",
                Action="lambda:InvokeFunctionUrl",
                Principal="*",
                FunctionUrlAuthType="NONE",
            )

            return function
        except clients.lmb.exceptions.ResourceConflictException:
            function = clients.lmb.update_function_configuration(
                FunctionName=self.event.detail.repository_name,
                Role=role_arn,
                Description=f"sententially deployed {self.event.detail.repository_name}:{self.event.detail.image_tag}",
                Environment={
                    "Variables": {"PREFIX": self.event.detail.repository_name}
                },
            )

            clients.lmb.get_waiter("function_updated_v2").wait(
                FunctionName=self.event.detail.repository_name
            )

            clients.lmb.update_function_code(
                FunctionName=self.event.detail.repository_name,
                ImageUri=f"{self.repository_url}:{self.event.detail.image_tag}",
                Publish=True,
            )

            try:
                clients.lmb.remove_permission(
                    FunctionName=self.event.detail.repository_name,
                    StatementId="FunctionURLAllowPublicAccess",
                )
            except clients.lmb.exceptions.ResourceNotFoundException:
                print(f"lambda permission does not exist")

            clients.lmb.add_permission(
                FunctionName=self.event.detail.repository_name,
                StatementId="FunctionURLAllowPublicAccess",
                Action="lambda:InvokeFunctionUrl",
                Principal="*",
                FunctionUrlAuthType="NONE",
            )

            return function

    def ensure(self):
        self._configure_perms()
        self._configure_lambda()
        print(self._put_url())

    def destroy(self):
        try:
            clients.lmb.delete_function_url_config(
                FunctionName=self.event.detail.repository_name
            )
        except clients.lmb.exceptions.ResourceNotFoundException:
            print(f"lambda url does not exist")

        try:
            clients.lmb.delete_function(FunctionName=self.event.detail.repository_name)
        except clients.lmb.exceptions.ResourceNotFoundException:
            print(f"lambda does not exist")

        try:
            clients.iam.detach_role_policy(
                PolicyArn=self.policy_arn, RoleName=self.spec.role_name
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
            print(f"policy does not exist")

        try:
            clients.iam.delete_role(RoleName=self.spec.role_name)
        except clients.iam.exceptions.NoSuchEntityException:
            print(f"role does not exist")
