from time import sleep
from sentential.lib.ecr import Image
from sentential.lib.clients import clients
from sentential.lib.shapes.aws import ECREvent, LAMBDA_ROLE_POLICY_JSON

class Infra:
    def __init__(self, event: ECREvent) -> None:
        self.image = Image(event)
        self.policy_arn = (
            f"arn:aws:iam::{event.account}:policy/{self.image.spec.policy_name}"
        )

    def _put_role(self):
        try:
            role = clients.iam.create_role(
                RoleName=self.image.spec.role_name,
                AssumeRolePolicyDocument=LAMBDA_ROLE_POLICY_JSON,
            )
            print("waiting for role to exist")
            clients.iam.get_waiter("role_exists").wait(RoleName=self.image.spec.role_name)
            return role
        except clients.iam.exceptions.EntityAlreadyExistsException:
            clients.iam.update_assume_role_policy(
                RoleName=self.image.spec.role_name,
                PolicyDocument=LAMBDA_ROLE_POLICY_JSON,
            )
            clients.iam.get_waiter("role_exists").wait(RoleName=self.image.spec.role_name)
            role = clients.iam.get_role(RoleName=self.image.spec.role_name)
            return role

    def _put_policy(self):
        try:
            policy = clients.iam.create_policy(
                PolicyName=self.image.spec.policy_name,
                PolicyDocument=self.image.spec.policy.json(exclude_none=True, by_alias=True),
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
                PolicyDocument=self.image.spec.policy.json(exclude_none=True, by_alias=True),
                SetAsDefault=True,
            )
            clients.iam.get_waiter("policy_exists").wait(PolicyArn=self.policy_arn)
            return clients.iam.get_policy(PolicyArn=self.policy_arn)

    def _put_url(self):
        try:
            clients.lmb.create_function_url_config(
                FunctionName=self.image.name,
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
                FunctionName=self.image.name,
                AuthType="NONE",
                Cors={
                    "AllowHeaders": ["*"],
                    "AllowMethods": ["*"],
                    "AllowOrigins": ["*"],
                    "ExposeHeaders": ["*"],
                },
            )

        return clients.lmb.get_function_url_config(
            FunctionName=self.image.name
        )["FunctionUrl"]

    def _configure_perms(self):
        role = self._put_role()
        policy = self._put_policy()
        clients.iam.attach_role_policy(
            RoleName=role["Role"]["RoleName"], PolicyArn=policy["Policy"]["Arn"]
        )

    def _configure_lambda(self):
        role_arn = clients.iam.get_role(RoleName=self.image.spec.role_name)["Role"]["Arn"]
        sleep(10)
        try:
            function = clients.lmb.create_function(
                FunctionName=self.image.name,
                Role=role_arn,
                PackageType="Image",
                Code={
                    "ImageUri": self.image.uri
                },
                Description=f"sententially deployed {self.image.name}:{self.image.tag}",
                Environment={
                    "Variables": {"PREFIX": self.image.name}
                },
                Architectures=[self.image.architecture],
            )

            clients.lmb.add_permission(
                FunctionName=self.image.name,
                StatementId="FunctionURLAllowPublicAccess",
                Action="lambda:InvokeFunctionUrl",
                Principal="*",
                FunctionUrlAuthType="NONE",
            )

            return function
        except clients.lmb.exceptions.ResourceConflictException:
            function = clients.lmb.update_function_configuration(
                FunctionName=self.image.name,
                Role=role_arn,
                Description=f"sententially deployed {self.image.name}:{self.image.tag}",
                Environment={
                    "Variables": {"PREFIX": self.image.name}
                },
            )

            clients.lmb.get_waiter("function_updated_v2").wait(
                FunctionName=self.image.name
            )

            clients.lmb.update_function_code(
                FunctionName=self.image.name,
                ImageUri=self.image.uri,
                Publish=True,
            )

            try:
                clients.lmb.remove_permission(
                    FunctionName=self.image.name,
                    StatementId="FunctionURLAllowPublicAccess",
                )
            except clients.lmb.exceptions.ResourceNotFoundException:
                print(f"lambda permission does not exist")

            clients.lmb.add_permission(
                FunctionName=self.image.name,
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
                FunctionName=self.image.name
            )
        except clients.lmb.exceptions.ResourceNotFoundException:
            print(f"lambda url does not exist")

        try:
            clients.lmb.delete_function(FunctionName=self.image.name)
        except clients.lmb.exceptions.ResourceNotFoundException:
            print(f"lambda does not exist")

        try:
            clients.iam.detach_role_policy(
                PolicyArn=self.policy_arn, RoleName=self.image.spec.role_name
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
            clients.iam.delete_role(RoleName=self.image.spec.role_name)
        except clients.iam.exceptions.NoSuchEntityException:
            print(f"role does not exist")
