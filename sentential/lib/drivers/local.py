import os
from tempfile import TemporaryDirectory
from typing import Dict, List
from sentential.lib.clients import clients
from sentential.lib.drivers.spec import Driver
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Image, Function
from sentential.lib.template import Policy
from python_on_whales.components.image.cli_wrapper import Image as DriverImage


#
# NOTE: Docker images locally are primary key'd (conceptually) off of their id, this is normalized by the Image type
#

class LocalDriverError(BaseException):
    pass


class LocalDriver(Driver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology

    def build(self, version: str) -> Image:
        built_image = clients.docker.build(
            self.ontology.context.path.root,
            load=True,
            tags=[
                f"{self.ontology.context.repository_name}:{version}"
            ],
            build_args=self.ontology.args.as_dict(),
        )

        if isinstance(built_image, DriverImage):
            return self._image_where_id(built_image.id)
        else:
            raise LocalDriverError("build returned unexpected type")

    def publish(self, version: str) -> str:
        image = self.image(version)
        repo_url = self.ontology.context.repository_url
        shipping_tag = f"{repo_url}:{version}"
        clients.docker.tag(image.id, shipping_tag)
        clients.docker.push(shipping_tag)
        return f"published {image.id} as {shipping_tag}"

    def images(self) -> List[Image]:
        images = []
        for id, image in self._docker_data().items():
            images.append(
                Image(
                    id=id,
                    digest=image['digest'],
                    tags=image['tags'],
                    versions=image['versions'],
                )  # arch=image.architecture
            )
        return images

    def image(self, version: str) -> Image:
        for image in self.images():
            if version in image.versions:
                return image
        raise LocalDriverError(f"no image found with where version {version}")

    def deployed(self) -> Function:
        # TODO: "sentential" container name is not a good enough matching mechanism
        running = [c for c in clients.docker.ps() if c.name == "sentential"]
        public_url = [c for c in clients.docker.ps() if c.name == "sentential-gw"]
        if running:
            container = running[0]
            running_image = clients.docker.image.inspect(container.image)
            image = self._image_where_id(running_image.id)
            
            if public_url:
                public_url = "http://localhost:8081"
            else:
                public_url = None

            return Function(
                image=image,
                function_name="local",
                arn="local",
                public_url=public_url
            )
        raise LocalDriverError(f"no image found with container name sentential")

    def deploy(self, image: Image, public_url: bool) -> str:
        self.destroy()
        clients.docker.network.create("sentential-bridge")
        credentials = self._get_federation_token()
        default_env = {
            "AWS_REGION": self.ontology.context.region,
            "PARTITION": self.ontology.envs.path,
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

    def _docker_data(self) -> Dict:
        docker_data = {}
        repo_name = self.ontology.context.repository_name
        for image in clients.docker.images():
            # strip versions
            repo_names_w_url = [tag.split(":")[0] for tag in image.repo_tags]
            # strip urls
            repo_names = [tag.split("/")[-1] for tag in repo_names_w_url]
            # match against known repo name
            match = any([repo_name == name for name in repo_names ])

            if match: 
                digest = None
                for proposed_digest in image.repo_digests:
                    proposed_digest = proposed_digest.split("@")[-1]

                    # safety: if assumption that image id and image digest are always tightly coupled is untrue, raise plz
                    if digest is not None:
                        if digest != proposed_digest:
                            raise LocalDriverError("image id and image digest not tightly coupled")
                    
                    digest = proposed_digest
                
                versions = []
                for tag in image.repo_tags:
                    versions.append(tag.split(":")[-1])

                docker_data[image.id]={
                    'id': image.id,
                    'digest': digest,
                    'tags': image.repo_tags,
                    'versions': versions
                }

        return docker_data

    def _image_where_id(self, id: str) -> Image:
        for image in self.images():
            if id == image.id:
                return image
        raise LocalDriverError(f"no image found with for id {id}")