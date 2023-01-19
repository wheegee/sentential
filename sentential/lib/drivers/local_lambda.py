import os
from sys import platform
from typing import Dict, Union
from sentential.lib.clients import clients
from sentential.lib.drivers.local_bridge import LocalBridge
from sentential.lib.template import Policy
from sentential.lib.ontology import Ontology
from sentential.lib.exceptions import LocalDriverError
from sentential.lib.drivers.spec import LambdaDriver
from python_on_whales.components.image.cli_wrapper import Image
from python_on_whales.components.container.cli_wrapper import Container

from sentential.lib.shapes import (
    AWSAssumeRole,
    AWSCredentials,
    AWSFederationToken,
    LambdaInvokeResponse,
)


class LocalLambdaDriver(LambdaDriver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology

    def deploy(self, image: Image, inject_env: Dict[str, str] = {}) -> str:
        LocalBridge.setup()  # hoist to cli callback when things are more generalized
        self.destroy()
        self.ontology.envs.export_defaults()
        credentials = self._get_credentials()
        credentials_env = {
            "AWS_LAMBDA_FUNCTION_NAME": self.ontology.context.resource_name,
            "AWS_ACCESS_KEY_ID": credentials.AccessKeyId,
            "AWS_SECRET_ACCESS_KEY": credentials.SecretAccessKey,
        }

        if credentials.SessionToken:
            credentials_env["AWS_SESSION_TOKEN"] = credentials.SessionToken

        hosts = []
        # required to properly resolve `host.docker.internal` in Linux
        if platform == "linux":
            hosts = [("host.docker.internal", "host-gateway")]

        default_env = {
            "AWS_REGION": self.ontology.context.region,
            "PARTITION": self.ontology.envs.path,
        }

        clients.docker.run(
            image.id,
            add_hosts=hosts,
            name=LocalBridge.config.lambda_name,
            hostname=LocalBridge.config.lambda_name,
            networks=[LocalBridge.config.bridge_name],
            detach=True,
            remove=False,
            publish=[
                (
                    LocalBridge.config.lambda_port,
                    LocalBridge.config.lambda_internal_port,
                )
            ],
            envs={**default_env, **credentials_env, **inject_env},
        )

        return f"deployed {self.ontology.context.resource_name} to local"

    def destroy(self) -> None:
        clients.docker.remove(
            [LocalBridge.config.lambda_name, LocalBridge.config.gw_name],
            force=True,
            volumes=True,
        )

    def logs(self, follow: bool = False):
        cmd = ["docker", "logs", LocalBridge.config.lambda_name]
        if follow:
            cmd.append("--follow")
        os.system(" ".join(cmd))

    def invoke(self, payload: str) -> str:
        local = clients.boto3.client(
            "lambda", endpoint_url=f"http://localhost:{LocalBridge.config.lambda_port}"
        )
        response = local.invoke(
            FunctionName="function", Payload=payload, LogType="Tail"
        )
        response["Payload"] = response["Payload"].read()
        response["Payload"] = response["Payload"].decode("utf-8")
        return LambdaInvokeResponse(**response).json()

    def _get_credentials(self) -> AWSCredentials:
        policy_json = Policy(self.ontology).render()
        identity = self.ontology.context.caller_identity
        session = clients.boto3.Session()
        session_creds = session.get_credentials()
        fallback = AWSCredentials(
            AccessKeyId=session_creds.access_key,
            SecretAccessKey=session_creds.secret_key,
            SessionToken=session_creds.token,
            Expiration=None,
        )

        try:
            if identity.type == "user":
                response = clients.sts.get_federation_token(
                    Name=f"{self.ontology.context.repository_name}-spec-policy",
                    Policy=policy_json,
                )
                return AWSFederationToken(**response).Credentials

            elif identity.type == "assumed-role":
                role_arn = "/".join(identity.Arn.split("/")[:-1]).replace(
                    "assumed-role", "role"
                )
                response = clients.sts.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName=f"{self.ontology.context.partition}-local-emulation",
                    Policy=policy_json,
                )
                return AWSAssumeRole(**response).Credentials

            else:
                raise LocalDriverError("neither federation nor self assume worked")

        except:
            print("WARNING: using unscoped credentials for local deployment")
            return fallback
