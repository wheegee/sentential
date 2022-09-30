import os
from tempfile import TemporaryDirectory
from typing import List
from sentential.lib.clients import clients
from sentential.lib.drivers.spec import Driver
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Image
from sentential.lib.template import Policy
from python_on_whales.components.image.cli_wrapper import Image as DriverImage


class LocalDriverError(BaseException):
    pass


class LocalDriver(Driver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology

    def build(self, version: str) -> Image:
        image = clients.docker.build(
            self.ontology.context.path.root,
            load=True,
            tags=[
                f"{self.ontology.context.repository_name}:{version}"
            ],  # build with local handle format
            build_args=self.ontology.args.as_dict(),
        )

        if isinstance(image, DriverImage):
            return Image(id=image.id, tags=image.repo_tags, arch=image.architecture)
        else:
            raise LocalDriverError("build returned unexpected type")

    def images(self) -> List[Image]:
        images = []
        repo_name = self.ontology.context.repository_name
        repo_url = self.ontology.context.repository_url
        for image in clients.docker.images():
            match = any(
                [repo_name == tag.split(":")[0] for tag in image.repo_tags]
            ) or any([repo_url == tag.split(":")[0] for tag in image.repo_tags])

            if match:
                images.append(
                    Image(id=image.id, tags=image.repo_tags, arch=image.architecture)
                )
        return images

    def image(self, version: str) -> Image:
        for image in self.images():
            if any(version == tag.split(":")[1] for tag in image.tags):
                return image
        raise LocalDriverError(f"no image found with for version {version}")

    def publish(self, version: str) -> Image:
        image = self.image(version)
        clients.docker.push(f"{self.ontology.context.repository_url}:{version}")
        return image

    def deployed(self) -> Image:
        running = [c for c in clients.docker.ps() if c.name == "sentential"]
        if running:
            container = running[0]
            image = clients.docker.image.inspect(container.image)
            return Image(id=image.id, tags=image.repo_tags, arch=image.architecture)
        else:
            raise LocalDriverError("could not find locally deployed function")

    def deploy(self, image: Image, public_url: bool) -> str:
        self.destroy()

        clients.docker.network.create("sentential-bridge")
        credentials = self._get_federation_token()
        default_env = {
            "AWS_REGION": self.ontology.context.region,
            "PARTITION": self.ontology.context.partition,
        }

        clients.docker.run(
            image.id,
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
            return "http://localhost:8081"
        else:
            return "http://localhost:9000"

    def destroy(self):
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

    def invoke(self, payload: str):
        # TODO: move away from shell-out here
        with TemporaryDirectory() as tmp:
            cmd = [
                "aws",
                "lambda",
                "invoke",
                "--function-name",
                "function",
                "--endpoint",
                "http://localhost:9000",
                "--log-type",
                "Tail",
                "--invocation-type",
                "RequestResponse",
                "--cli-binary-format",
                "raw-in-base64-out",
                "--payload",
                f"'{payload}'",
                f"{tmp}/output",
            ]
            os.system(" ".join(cmd))
            os.system(f"cat {tmp}/output")

    def _get_federation_token(self):
        policy_json = Policy(self.ontology).render()
        token = clients.sts.get_federation_token(
            Name=f"{self.ontology.context.repository_name}-spec-policy",
            Policy=policy_json,
        )["Credentials"]

        return {
            "AWS_ACCESS_KEY_ID": token["AccessKeyId"],
            "AWS_SECRET_ACCESS_KEY": token["SecretAccessKey"],
            "AWS_SESSION_TOKEN": token["SessionToken"],
        }
