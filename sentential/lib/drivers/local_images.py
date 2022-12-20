from functools import lru_cache
from time import sleep
from sentential.lib.ontology import Ontology
from sentential.lib.clients import clients
from sentential.lib.shapes import CURRENT_WORKING_IMAGE_TAG, Architecture, Image
from sentential.lib.exceptions import LocalDriverError
from python_on_whales.components.image.cli_wrapper import Image as PythonOnWhalesImage

import python_on_whales
from typing import Any, List, Dict, Optional, Tuple, Union


class LocalImagesDriver:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.repo_name = ontology.context.repository_name
        self.repo_url = ontology.context.repository_url

    def build(self, arch: str) -> Image:
        platform = f"linux/{arch}"
        manifest_uri = f"{self.repo_name}:{CURRENT_WORKING_IMAGE_TAG}"
        cwi = self._build(manifest_uri, platform)
        return self.image_by_id(cwi.id)

    def publish(self, tag: str, arch: List[str]) -> str:
        platforms = [f"linux/{a}" for a in arch]
        manifest_list_uri = f"{self.repo_url}:{tag}"
        image_manifest_uris = []
        built: List[Image] = []
        cwi = self.image_by_tag(CURRENT_WORKING_IMAGE_TAG)

        for platform in platforms:
            image_manifest_uri = f"{manifest_list_uri}-{platform.split('/')[1]}"
            image = self._build(image_manifest_uri, platform)
            image_manifest_uris.append(image_manifest_uri)
            built.append(image)

        if cwi.id not in [build.id for build in built]:
            raise LocalDriverError(
                "current working image id does not match that of any final build"
            )

        for image_manifest_uri in image_manifest_uris:
            clients.docker.push(image_manifest_uri)

        sleep(2)
        clients.docker.manifest.create(manifest_list_uri, image_manifest_uris, True)
        clients.docker.manifest.push(manifest_list_uri, True)
        return manifest_list_uri

    def _build(self, tag: str, platform: str) -> Image:
        self.ontology.args.export_defaults()  # maybe hoist to initializer?

        cmd = {
            "tags": [tag],
            "platforms": [platform],
            "load": True,
            "build_args": self.ontology.args.as_dict(),
        }

        image = clients.docker.build(self.ontology.context.path.root, **cmd)

        if isinstance(image, PythonOnWhalesImage):
            return self.image_by_id(image.id)
        else:
            raise LocalDriverError("docker build driver returned unexpected type")

    def pull(self, image: Image) -> List[str]:
        tags_pulled = []
        for tag in image.tags:
            if self.ontology.context.repository_url in tag:
                clients.docker.pull(tag)
                tags_pulled.append(tag)
        return tags_pulled

    def images(self) -> List[Image]:
        images: List[Image] = []
        for id, digest in self._image_identifiers():
            images.append(
                Image(
                    id=id,
                    digest=digest,
                    uri=None,
                    tags=self._get_tags(id),
                    versions=self._get_tags(id),
                    arch=self._get_arch(id),
                )
            )
        return images

    def clean(self) -> None:
        for image in self.images():
            clients.docker.container.remove("sentential", force=True)
            clients.docker.image.remove(image.id, force=True)

    def image_by_tag(self, tag: str, arch: str = "any") -> Image:
        return self._image_by("tags", tag, arch)

    def image_by_digest(self, digest: str, arch: str = "any") -> Image:
        return self._image_by("digest", digest, arch)

    def image_by_id(self, id: str, arch: str = "any") -> Image:
        return self._image_by("id", id, arch)

    def _image_by(self, attribute: str, value: str, arch: str = "any") -> Image:
        results = []
        images = self.images()
        humanized_value = value.replace("sha256:", "")[0:12]
        clause = None

        if arch != "any":
            images = [image for image in images if image.arch == arch]

        for image in self.images():
            attr = getattr(image, attribute)
            if isinstance(attr, list):
                clause = f"{humanized_value} in {attribute}"
                if value in attr:
                    results.append(image)
            elif isinstance(attr, str):
                clause = f"{attribute} is {humanized_value}"
                if value == attr:
                    results.append(image)
            else:
                raise LocalDriverError("unhandled type in image query")

        if len(results) == 0:
            raise LocalDriverError(f"no images found where {clause} and arch is {arch}")
        elif len(results) > 1:
            raise LocalDriverError(f"ambiguous match where {clause} and arch is {arch}")
        else:
            return results[0]

    def _get_tags(self, image_id: str) -> List[str]:
        return self._tag_map()[image_id]

    def _get_arch(self, image_id: str) -> str:
        return self._arch_map()[image_id]

    def _repo_images(
        self,
    ) -> List[python_on_whales.Image]:  # pyright: ignore[reportPrivateImportUsage]
        images = []
        for image in clients.docker.images():
            # strip tags
            repo_names_w_url = [tag.split(":")[0] for tag in image.repo_tags]
            # strip urls
            repo_names = [tag.split("/")[-1] for tag in repo_names_w_url]
            # match against known repo name
            match = any([self.repo_name == name for name in repo_names])

            if match:
                images.append(image)

        return images

    def _image_identifiers(self) -> List[Tuple[str, str]]:
        pairs = []
        for image in self._repo_images():
            image_id = image.id
            if image.repo_digests:
                image_digest = image.repo_digests[0].split("@")[-1]
            else:
                image_digest = None

            pairs.append((image_id, image_digest))
        return list(set(pairs))

    def _tag_map(self) -> Dict[str, List[str]]:
        tags = {}
        for image in self._repo_images():
            image_tags = list(set([tag.split(":")[-1] for tag in image.repo_tags]))
            if image.id in tags.keys():
                tags[image.id] = tags[image.id] + image_tags
            else:
                tags[image.id] = image_tags
        return tags

    def _arch_map(self) -> Dict[str, str]:
        return {image.id: image.architecture for image in self._repo_images()}
