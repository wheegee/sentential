import typer
import json
from python_on_whales import DockerException
from pipes import Template
from typing import List
from sentential.lib.clients import clients
from sentential.lib.shapes.internal import Spec
from sentential.lib.facts import Factual, Facts
from jinja2 import Template
from sentential.lib.store import ConfigStore


class Image(Factual):
    def __init__(self, tag: str) -> None:
        super().__init__()
        self.repository_name = self.facts.repository_name
        self.tag = tag

    def spec(self) -> Spec:
        metadata = self._fetch_metadata()
        spec_data = json.loads(metadata.config.labels["spec"])
        return Spec(**spec_data)

    def arch(self) -> str:
        metadata = self._fetch_metadata()
        if metadata.architecture == "amd64":
            return "x86_64"
        else:
            return metadata.architecture

    def _fetch_metadata(self):
        return clients.docker.image.inspect(f"{self.facts.repository_name}:{self.tag}")

    @classmethod
    def build(cls, tag: str = "latest") -> None:
        facts = Facts()
        clients.docker.build(
            f"{facts.path.root}",
            # TODO: replace labels with github metadata?
            # labels={
            #     "spec": Spec(
            #         prefix=self.facts.repository_name,
            #         policy=json.loads(self.facts.path.policy.read_text()),
            #         role_name=self.facts.repository_name,
            #         policy_name=self.facts.repository_name,
            #     ).json(exclude_none=True)
            # },
            load=True,
            tags=[f"{facts.repository_name}:{tag}"],
        )
        return cls(tag)


class Lambda(Factual):
    def __init__(self, image: Image, partition: str) -> None:
        super().__init__()
        self.image = image
        self.partition = partition

    def deploy(self, http: bool = True):
        self.destroy()
        self.image.build()
        clients.docker.network.create("sentential-bridge")
        credentials = self._get_federation_token()
        default_env = {
            "AWS_REGION": self.facts.region,
            "PARTITION": f"{self.partition}/{self.image.repository_name}",
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

        if http:
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

        if http:
            print("gateway: http://localhost:8081")
        else:
            print("lambda: http://localhost:9000")

    def destroy(self):
        clients.docker.remove(["sentential"], force=True, volumes=True)
        clients.docker.remove(["sentential-gw"], force=True, volumes=True)
        try:
            clients.docker.network.remove(["sentential-bridge"])
        except:
            pass

    def _get_federation_token(self):
        policy_json = Template(self.facts.path.policy.read_text()).render(
            partition=self.partition,
            facts=self.facts,
            config=ConfigStore(self.partition).parameters(),
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
    def __init__(self, image: Image) -> None:
        super().__init__()
        self.image = image

    def images(self) -> List:
        images = clients.docker.image.list({"label": "spec"})
        filtered = []
        for image in images:
            for repo_tag in image.repo_tags:
                repository_name, tag = repo_tag.split(":")
                if repository_name == self.facts.repository_name:
                    filtered.append(Image(repository_name, tag))
        return filtered

    @retry_after_docker_login
    def publish(self):
        self.image.build()
        clients.docker.image.tag(
            f"{self.facts.repository_name}:{self.image.tag}",
            f"{self.facts.repository_url}:{self.image.tag}",
        )
        clients.docker.image.push(f"{self.facts.repository_url}:{self.image.tag}")
