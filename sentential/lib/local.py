import json
import typer
from python_on_whales import DockerException
from pipes import Template
from typing import List
from sentential.lib.clients import clients
from sentential.lib.shapes.internal import Spec
from sentential.lib.facts import Factual, Facts
from jinja2 import Template
from sentential.lib.store import Env, Arg
from IPython import embed
from sentential.lib.facts import lazy_property

class Image(Factual):
    def __init__(self, tag: str) -> None:
        super().__init__()
        self.repository_name = self.facts.repository_name
        self.tag = tag

    @lazy_property
    def id(self) -> str:
        return self.metadata.id

    @lazy_property
    def tags(self) -> List[str]:
        return [tag.split(":")[1] for tag in self.metadata.repo_tags ]

    @lazy_property
    def arch(self) -> str:
        if self.metadata.architecture == "amd64":
            return "x86_64"
        else:
            return self.metadata.architecture

    @lazy_property
    def metadata(self):
        return clients.docker.image.inspect(f"{self.repository_name}:{self.tag}")

    @classmethod
    def build(cls, tag: str = "latest") -> None:
        facts = Facts()
        clients.docker.build(
            f"{facts.path.root}",
            load=True,
            tags=[f"{facts.repository_name}:{tag}"],
            build_args=Arg().as_dict(),
        )
        return cls(tag)


class Lambda(Factual):
    def __init__(self, image: Image) -> None:
        super().__init__()
        self.image = image

    @classmethod
    def deployed(cls):
        for container in clients.docker.ps():
            if container.name == "sentential":
                inspect = clients.docker.image.inspect(container.image)
                tag = inspect.repo_tags[0].split(":")[1]
                return cls(Image(tag))

    def deploy(self, public_url: bool = True):
        self.destroy()
        self.image.build(self.image.tag)
        clients.docker.network.create("sentential-bridge")
        credentials = self._get_federation_token()
        default_env = {
            "AWS_REGION": self.facts.region,
            "PARTITION": Env().chamber_path,
        }

        clients.docker.run(
            f"{self.image.repository_name}:{self.image.tag}",
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
            env=Env().parameters(),
        )
        token = clients.sts.get_federation_token(
            Name=f"{self.image.repository_name}-spec-policy",
            Policy=policy_json,
        )["Credentials"]

        return {
            "AWS_ACCESS_KEY_ID": token["AccessKeyId"],
            "AWS_SECRET_ACCESS_KEY": token["SecretAccessKey"],
            "AWS_SESSION_TOKEN": token["SessionToken"],
        }

    def logs(self, follow: bool = False):
        return clients.docker.logs("sentential", follow=follow)


def retry_after_docker_login(func):
    def wrap(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (DockerException) as e:
            print("retrying after ecr login")
            clients.docker.login_ecr()
            return func(self, *args, **kwargs)

    return wrap


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
        image.build(image.tag)
        clients.docker.image.tag(
            f"{self.facts.repository_name}:{image.tag}",
            f"{self.facts.repository_url}:{image.tag}",
        )
        clients.docker.image.push(f"{self.facts.repository_url}:{image.tag}")
