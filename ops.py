import json
import os
from typing import Dict, List, Optional
from pathlib import Path, PosixPath
from os import makedirs
from os.path import exists
from base64 import b64decode, b64encode
from python_on_whales import DockerClient, docker
import boto3
from pydantic import BaseModel, validator
from jinja2 import Environment, FileSystemLoader, Template
import requests


class PathConfig(BaseModel):
    root: PosixPath
    src: PosixPath
    dockerfile: PosixPath
    wrapper: PosixPath
    policy: PosixPath


class Config(BaseModel):
    function: str
    runtime: Optional[str]
    path: Optional[PathConfig]
    region: str = boto3.session.Session().region_name
    account_id: str = boto3.client("sts").get_caller_identity().get("Account")
    kms_key_id: str = [
        ssm_key["TargetKeyId"]
        for ssm_key in boto3.client("kms").list_aliases()["Aliases"]
        if ssm_key["AliasName"] == "alias/aws/ssm"
    ][0]
    repository_url: Optional[str]
    registry_url: Optional[str]

    @validator("repository_url", always=True)
    def assemble_repository_url(cls, v, values) -> str:
        return f"{values['account_id']}.dkr.ecr.{values['region']}.amazonaws.com/{values['function']}"

    @validator("registry_url", always=True)
    def assemble_registry_url(cls, v, values) -> str:
        return f"{values['account_id']}.dkr.ecr.{values['region']}.amazonaws.com"

    @validator("path", always=True)
    def assemble_path(cls, v, values) -> str:
        root = Path(f"lambdas/{values['function']}")
        return PathConfig(
            root=root,
            src=Path(f"{root}/src"),
            dockerfile=Path(f"{root}/Dockerfile"),
            wrapper=Path(f"{root}/wrapper.sh"),
            policy=Path(f"{root}/policy.json"),
        )


class Clients:
    def __init__(self) -> None:
        self.docker = docker
        self.sts = boto3.client("sts")
        self.ecr = boto3.client("ecr")

    def docker(self):
        return self.docker

    def sts(self):
        return self.sts

    def ecr(self):
        return self.ecr


class BoilerPlate:
    def __init__(self, config: Config):
        self.config = config
        self.jinja = Environment(loader=FileSystemLoader("templates"))
        if not exists(Path(self.config.path.src)):
            makedirs(self.config.path.src)

    def write(self, template: Template, write_to: PosixPath) -> PosixPath:
        if not exists(write_to):
            with open(write_to, "w+") as f:
                f.writelines(template.render(config=self.config))

        return write_to

    def all(self, runtime: str):
        self.dockerfile(runtime)
        self.wrapper()
        self.policy()

    def dockerfile(self, image: str):
        self.config.runtime = image
        self.write(self.jinja.get_template("Dockerfile"), self.config.path.dockerfile)

    def wrapper(self):
        self.write(self.jinja.get_template("wrapper.sh"), self.config.path.wrapper)

    def policy(self):
        self.write(self.jinja.get_template("policy.json"), self.config.path.policy)


class Sentential:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = Clients()
        self.template = BoilerPlate(self.config)

    def init(self, runtime: str) -> None:
        self.template.all(runtime)

    def build(self):
        b64policy = b64encode(self.config.path.policy.read_bytes()).decode("utf-8")
        self.client.docker.build(
            f"{self.config.path.root}",
            tags=[f"{self.config.function}:local"],
            labels={"spec.prefix": f"{self.config.function}", "spec.policy": b64policy},
        )

    def test(self):
        self.client.docker.remove([f"{self.config.function}"], force=True, volumes=True)
        image = self.client.docker.image.inspect(f"{self.config.function}:local")
        policy = (
            b64decode(image.config.labels["spec.policy"])
            .decode("utf-8")
            .replace("\n", "")
        )
        prefix = image.config.labels["spec.prefix"]
        credentials = self.client.sts.get_federation_token(
            Name=f"{self.config.function}-spec-policy", Policy=policy
        )["Credentials"]
        self.client.docker.container.run(
            f"{self.config.function}:local",
            name=f"{self.config.function}",
            detach=True,
            remove=False,
            publish=[("9000", "8080")],
            envs={
                "AWS_REGION": self.config.region,
                "PREFIX": prefix,
                "AWS_ACCESS_KEY_ID": credentials["AccessKeyId"],
                "AWS_SECRET_ACCESS_KEY": credentials["SecretAccessKey"],
                "AWS_SESSION_TOKEN": credentials["SessionToken"],
            },
        )

    def publish(self, version: str = "latest"):
        self.client.docker.login_ecr()
        self.client.docker.image.tag(
            f"{self.config.function}:local", f"{self.config.repository_url}:{version}"
        )
        self.client.docker.image.push(f"{self.config.repository_url}:{version}")

    def ecr_api_get(self, url: str):
        config_json = json.loads(
            open(os.path.expanduser("~/.docker/config.json")).read()
        )
        auth = f"Basic {config_json['auths'][self.config.registry_url]['auth']}"
        return requests.get(
            url,
            headers={
                "Authorization": auth,
                "Accept": "application/vnd.docker.distribution.manifest.v2+json",
            },
        )

    def deploy(self, version: str = "latest"):
        response = self.ecr_api_get(
            f"https://{self.config.registry_url}/v2/{self.config.function}/manifests/{version}"
        )
        manifest = response.json()
        digest = manifest["config"]["digest"]
        response = self.ecr_api_get(
            f"https://{self.config.registry_url}/v2/{self.config.function}/blobs/{digest}"
        )
        return json.dumps(response.json()["config"]["Labels"])


config = Config(function="kaixo")
sentential = Sentential(config)
# sentential.init("amazon/aws-lambda-ruby")
# sentential.build()
# sentential.test()
# sentential.publish()
print(sentential.deploy())
