from distutils.version import LooseVersion
import re
from python_on_whales import DockerException
from pipes import Template
from typing import List
from sentential.lib.clients import clients
from sentential.lib.const import CWI_TAG, SEMVER_REGEX
from sentential.lib.facts import Factual, Facts
from jinja2 import Template
from sentential.lib.store import Env, Arg
from sentential.lib.facts import lazy_property
import os


def retry_after_docker_login(func):
    def wrap(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (DockerException) as e:
            print("retrying after ecr login")
            clients.docker.login_ecr()
            return func(self, *args, **kwargs)

    return wrap


class Image(Factual):
    def __init__(self, tag: str) -> None:
        super().__init__()
        self.tag = tag

    @classmethod
    def build(cls, tag: str = "latest") -> None:
        facts = Facts()
        Arg().export_defaults()
        clients.docker.build(
            f"{facts.path.root}",
            load=True,
            tags=[f"{facts.repository_name}:{tag}"],  # build with local handle format
            build_args=Arg().as_dict(),
        )
        return cls(tag)

    @lazy_property
    def exists(self):
        try:
            self.metadata
            return True
        except:
            return False

    @lazy_property
    def id(self) -> str:
        if bool(self.metadata.repo_digests):
            # TODO: use registry_url to find element of list instead of assuming first
            return self.metadata.repo_digests[0].split("@")[1]
        else:
            return self.metadata.id

    @lazy_property
    def tags(self) -> List[str]:
        return [tag.split(":")[1] for tag in self.metadata.repo_tags]

    @lazy_property
    def arch(self) -> str:
        if self.metadata.architecture == "amd64":
            return "x86_64"
        else:
            return self.metadata.architecture

    @lazy_property
    def metadata(self):
        return clients.docker.image.inspect(f"{self.facts.repository_name}:{self.tag}")

    def label_for_shipment(self, tag: str):
        clients.docker.tag(
            f"{self.facts.repository_name}:{self.tag}",
            f"{self.facts.repository_url}:{tag}",
        )
        return Image(tag)


class Lambda(Factual):
    def __init__(self, image: Image) -> None:
        super().__init__()
        self.image = image
        self.env = Env()

    @classmethod
    def deployed(cls):
        for container in clients.docker.ps():
            if container.name == "sentential":
                inspect = clients.docker.image.inspect(container.image)
                tag = inspect.repo_tags[0].split(":")[1]
                return cls(Image(tag))

    @retry_after_docker_login
    def deploy(self, public_url: bool = True):
        self.destroy()
        self.env.export_defaults()

        if self.image.tag == CWI_TAG:
            image_label = f"{self.facts.repository_name}:{self.image.tag}"
        else:
            image_label = f"{self.facts.repository_url}:{self.image.tag}"

        clients.docker.network.create("sentential-bridge")
        credentials = self._get_federation_token()
        default_env = {
            "AWS_REGION": self.facts.region,
            "PARTITION": self.env.path,
        }

        clients.docker.run(
            image_label,
            name="sentential",
            hostname="sentential",
            networks=["sentential-bridge"],
            detach=True,
            remove=False,
            publish=[("9000", "8080")],
            envs={**default_env, **credentials},
        )

        if public_url:
            clients.docker.run(
                "ghcr.io/wheegee/sentential-gw:latest",
                name="sentential-gw",
                hostname="sentential-gw",
                networks=["sentential-bridge"],
                detach=True,
                remove=False,
                publish=[("8081", "8081")],
                envs={"LAMBDA_ENDPOINT": "http://sentential:8080"},
            )

        if public_url:
            print("http://localhost:8081")
        else:
            print("http://localhost:9000")

    def destroy(self):
        clients.docker.remove(["sentential"], force=True, volumes=True)
        clients.docker.remove(["sentential-gw"], force=True, volumes=True)
        try:
            clients.docker.network.remove(["sentential-bridge"])
        except:
            pass

    def _get_federation_token(self):
        policy_json = Template(self.facts.path.policy.read_text()).render(
            facts=self.facts,
            env=self.env.parameters(),
        )
        token = clients.sts.get_federation_token(
            Name=f"{self.facts.repository_name}-spec-policy",
            Policy=policy_json,
        )["Credentials"]

        return {
            "AWS_ACCESS_KEY_ID": token["AccessKeyId"],
            "AWS_SECRET_ACCESS_KEY": token["SecretAccessKey"],
            "AWS_SESSION_TOKEN": token["SessionToken"],
        }

    def logs(self, follow: bool = False):
        cmd = ["docker", "logs", "sentential"]
        if follow:
            cmd.append("--follow")
        os.system(" ".join(cmd))


class Repository(Factual):
    def __init__(self) -> None:
        super().__init__()

    def images(self) -> List[Image]:
        images = clients.docker.image.list()
        filtered = []
        for image in images:
            for repo_tag in image.repo_tags:
                repository_name, tag = repo_tag.split(":")
                if repository_name == self.facts.repository_name:
                    filtered.append(Image(tag))
        return filtered

    @retry_after_docker_login
    def publish(self, image: Image):
        clients.docker.image.push(f"{self.facts.repository_url}:{image.tag}")
