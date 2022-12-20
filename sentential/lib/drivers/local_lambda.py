from ctypes import Union
import json
import os
from tempfile import TemporaryDirectory
from typing import Dict
from sentential.lib.clients import clients
from sentential.lib.template import Policy
from sentential.lib.ontology import Ontology
from sentential.lib.exceptions import LocalDriverError
from sentential.lib.drivers.spec import LambdaDriver
from sentential.lib.shapes import (
    AWSAssumeRole,
    AWSCredentials,
    AWSFederationToken,
    Image,
    LambdaInvokeResponse,
)


#
# NOTE: Docker images locally are primary key'd (conceptually) off of their id, this is normalized by the Image type
#


class LocalLambdaDriver(LambdaDriver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology

    def deploy(self, image: Image, inject_env: Dict[str, str] = {}) -> Image:
        self.destroy()
        self.ontology.envs.export_defaults()
        clients.docker.network.create("sentential-bridge")
        credentials = self._get_credentials()
        credentials_env = {
            "AWS_LAMBDA_FUNCTION_NAME": self.ontology.context.resource_name,
            "AWS_ACCESS_KEY_ID": credentials.AccessKeyId,
            "AWS_SECRET_ACCESS_KEY": credentials.SecretAccessKey,
        }

        if credentials.SessionToken:
            credentials_env["AWS_SESSION_TOKEN"] = credentials.SessionToken

        default_env = {
            "AWS_REGION": self.ontology.context.region,
            "PARTITION": self.ontology.envs.path,
        }

        clients.docker.run(
            image.id,
            add_hosts=[("host.docker.internal", "host-gateway")],
            name="sentential",
            hostname="sentential",
            networks=["sentential-bridge"],
            detach=True,
            remove=False,
            publish=[("9000", "8080")],
            envs={**default_env, **credentials_env, **inject_env},
        )

        return image

    def destroy(self) -> None:
        clients.docker.remove(["sentential"], force=True, volumes=True)
        clients.docker.remove(["sentential-gw"], force=True, volumes=True)
        try:
            clients.docker.network.remove(["sentential-bridge"])
        except:
            pass

    def logs(self, follow: bool = False):
        cmd = ["docker", "logs", "sentential"]
        if follow:
            cmd.append("--follow")
        os.system(" ".join(cmd))

    def invoke(self, payload: str) -> LambdaInvokeResponse:
        local = clients.boto3.client("lambda", endpoint_url="http://localhost:9000")
        response = local.invoke(
            FunctionName="function", Payload=payload, LogType="Tail"
        )
        response["Payload"] = response["Payload"].read()
        response["Payload"] = response["Payload"].decode("utf-8")
        return LambdaInvokeResponse(**response)

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
