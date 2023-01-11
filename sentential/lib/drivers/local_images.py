from time import sleep
from typing import List, Union
from python_on_whales.components.image.cli_wrapper import Image
from sentential.lib.drivers.spec import ImagesDriver
from sentential.lib.shapes import CURRENT_WORKING_IMAGE_TAG, Architecture
from sentential.lib.ontology import Ontology
from sentential.lib.clients import clients
from sentential.lib.exceptions import LocalDriverError


class LocalImagesDriver(ImagesDriver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.repo_name = ontology.context.repository_name
        self.repo_url = ontology.context.repository_url

    def build(self, arch: Architecture) -> Image:
        platform = f"linux/{arch.value}"
        manifest_uri = f"{self.repo_name}:{CURRENT_WORKING_IMAGE_TAG}"
        self._build(manifest_uri, platform)
        return self.get_image()

    def publish(self, tag: str, arch: List[Architecture]) -> List[Image]:
        platforms = [f"linux/{a.value}" for a in arch]
        manifest_list_uri = f"{self.repo_url}:{tag}"
        image_manifest_uris = []
        built: List[Image] = []
        cwi = self.get_image()

        for platform in platforms:
            image_manifest_uri = f"{manifest_list_uri}-{platform.split('/')[1]}"
            image = self._build(image_manifest_uri, platform)
            image_manifest_uris.append(image_manifest_uri)
            built.append(image)

        if cwi.id not in [build.id for build in built]:
            raise LocalDriverError(
                "current working image id does not match that of any local build"
            )

        for image_manifest_uri in image_manifest_uris:
            clients.docker.push(image_manifest_uri)

        sleep(2)
        clients.docker.manifest.create(manifest_list_uri, image_manifest_uris, True)
        clients.docker.manifest.push(manifest_list_uri, False)
        return built

    def _build(self, tag: str, platform: str) -> Image:
        self.ontology.args.export_defaults()

        cmd = {
            "tags": [tag],
            "platforms": [platform],
            "load": True,
            "build_args": self.ontology.args.as_dict(),
        }

        image = clients.docker.build(self.ontology.context.path.root, **cmd)

        if isinstance(image, Image):
            return image
        else:
            raise LocalDriverError("docker build driver returned unexpected type")

    def get_image(self, tag: Union[str, None] = None) -> Image:
        if tag is None:
            tag = CURRENT_WORKING_IMAGE_TAG

        for image in clients.docker.images():
            if f"{self.repo_name}:{tag}" in image.repo_tags:
                return image

        if tag is not CURRENT_WORKING_IMAGE_TAG:
            pulled_image = clients.docker.pull(f"{self.repo_url}:{tag}")
            if isinstance(pulled_image, Image):
                pulled_image.tag(f"{self.repo_name}:{CURRENT_WORKING_IMAGE_TAG}")
                return pulled_image

        raise LocalDriverError(f"no image with {tag} tag found")

    def get_images(self) -> List[Image]:
        images = []
        for image in clients.docker.images():
            image_repo = image.repo_tags[0].split("/")[-1].split(":")[0]
            if self.repo_name == image_repo:
                images.append(image)
        return images

    def clean(self) -> None:
        images = clients.docker.images()
        repo_images = []
        clients.docker.container.remove("sentential", force=True)
        for image in images:
            for tag in image.repo_tags:
                if image not in repo_images:
                    if self.repo_name == tag.split("/")[-1].split(":")[0]:
                        repo_images.append(image)

        for image in repo_images:
            clients.docker.image.remove(image, force=True)
