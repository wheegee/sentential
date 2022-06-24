import json
import os
from typing import Optional
from pathlib import Path, PosixPath
from os import makedirs
from os.path import exists
from base64 import b64decode, b64encode
from python_on_whales import docker
from python_on_whales.exceptions import DockerException
import boto3
from pydantic import BaseModel, validator
from jinja2 import Environment, FileSystemLoader, Template
import requests
from requests import HTTPError
from shutil import which
from subprocess import run as shell


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

    def all(self, runtime: str):
        self.dockerfile(runtime)
        self.wrapper()
        self.policy()

    def dockerfile(self, image: str):
        self.config.runtime = image
        self._write(self.jinja.get_template("Dockerfile"), self.config.path.dockerfile)

    def wrapper(self):
        self._write(self.jinja.get_template("wrapper.sh"), self.config.path.wrapper)

    def policy(self):
        self._write(self.jinja.get_template("policy.json"), self.config.path.policy)

    def _write(self, template: Template, write_to: PosixPath) -> PosixPath:
        if not exists(write_to):
            with open(write_to, "w+") as f:
                f.writelines(template.render(config=self.config))

        return write_to


def retry_with_login(func):
    def wrap(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (DockerException, HTTPError) as e:
            print("retrying after ecr login")
            self.client.docker.login_ecr()
            return func(self, *args, **kwargs)

    return wrap


class ChamberWrapper:
    def __init__(self, config: Config):
        self.config = config
        if which("chamber") is None:
            raise SystemExit("please install chamber")

    def create(self, key, value):
        shell(["chamber", "write", self.config.function, key, value])

    update = create

    def read(self, key=None):
        if key is None:
            shell(["chamber", "list", self.config.function])
        else:
            shell(["chamber", "read", self.config.function, key])

    def delete(self, key):
        shell(["chamber", "delete", self.config.function, key])


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

    @retry_with_login
    def publish(self, version: str = "latest"):
        self.client.docker.image.tag(
            f"{self.config.function}:local", f"{self.config.repository_url}:{version}"
        )
        self.client.docker.image.push(f"{self.config.repository_url}:{version}")

    @retry_with_login
    def deploy(self, version: str = "latest"):
        response = self._ecr_api_get(
            f"https://{self.config.registry_url}/v2/{self.config.function}/manifests/{version}"
        )
        manifest = response.json()
        digest = manifest["config"]["digest"]
        response = self._ecr_api_get(
            f"https://{self.config.registry_url}/v2/{self.config.function}/blobs/{digest}"
        )
        return json.dumps(response.json()["config"]["Labels"])

    def _ecr_api_get(self, url: str):
        config_json = json.loads(
            open(os.path.expanduser("~/.docker/config.json")).read()
        )
        auth = f"Basic {config_json['auths'][self.config.registry_url]['auth']}"
        response = requests.get(
            url,
            headers={
                "Authorization": auth,
                "Accept": "application/vnd.docker.distribution.manifest.v2+json",
            },
        )
        response.raise_for_status()
        return response


# config = Config(function="kaixo")

# Container / Templating
# sentential = Sentential(config)
# sentential.init("amazon/aws-lambda-ruby")
# sentential.build()
# sentential.test()
# sentential.publish()
# print(sentential.deploy())

# Secrets Mgmt
# chamber = ChamberWrapper(config)
# chamber.read()
# chamber.create("secret", "sooperdoopersecret")
# chamber.update("secret", "justanaliasforcreate")
# chamber.delete("secret")
