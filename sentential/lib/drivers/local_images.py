from functools import lru_cache
from os import environ
from time import sleep
from sentential.lib.ontology import Ontology
from sentential.lib.clients import clients
from sentential.lib.shapes import Image
from sentential.lib.exceptions import LocalDriverError
from python_on_whales.components.image.cli_wrapper import Image as PythonOnWhalesImage

import python_on_whales
from typing import List, Dict, Tuple


class LocalImagesDriver:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.repo_name = ontology.context.repository_name
        self.repo_url = ontology.context.repository_url

    def build(self, tag: str, push: bool) -> List[Image]:
        if "PLATFORMS" in environ:
            return self._build_platforms(tag, environ["PLATFORMS"].split(","), push)
        else:
            return self._build(tag, push)

    def _build(self, tag: str, push: bool) -> List[Image]:
        self.ontology.args.export_defaults()

        clients.docker.build(
            self.ontology.context.path.root,
            load=True,
            tags=[f"{self.repo_url}:{tag}"] if push else [f"{self.repo_name}:{tag}"],
            build_args=self.ontology.args.as_dict(),
        )
        if push:
            clients.docker.push(f"{self.repo_url}:{tag}")

        return [self.image_by_tag(tag)]

    def _build_platforms(
        self, tag: str, platforms: List[str], push: bool
    ) -> List[Image]:
        self.ontology.args.export_defaults()

        images = []
        for platform in platforms:
            arch = platform.split("/")[1]
            tags = (
                [f"{self.repo_url}:{tag}-{arch}"]
                if push
                else [f"{self.repo_name}:{tag}-{arch}"]
            )
            clients.docker.build(
                self.ontology.context.path.root,
                platforms=[platform],
                load=True,
                tags=tags,
                build_args=self.ontology.args.as_dict(),
            )
            if push:
                clients.docker.push(f"{self.repo_url}:{tag}-{arch}")
                clients.docker.manifest.create(
                    f"{self.repo_url}:{tag}", [f"{self.repo_url}:{tag}-{arch}"], True
                )
                clients.docker.manifest.annotate(
                    f"{self.repo_url}:{tag}", f"{self.repo_url}:{tag}-{arch}", arch
                )

            sleep(2)  # TODO: fix this hack that waits for the image to become available
            images.append(self.image_by_tag(f"{tag}-{arch}"))
        if push:
            clients.docker.manifest.push(f"{self.repo_url}:{tag}", True)

        return images

    def pull(self, image: Image) -> List[str]:
        tags_pulled = []
        for tag in image.tags:
            if self.ontology.context.repository_url in tag:
                clients.docker.pull(tag)
                tags_pulled.append(tag)
        return tags_pulled

    def images(self) -> List[Image]:
        images = []
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

        self._repo_images.cache_clear()

    def image_by_tag(self, tag: str) -> Image:
        for image in self.images():
            if tag in image.tags:
                return image
        raise LocalDriverError(f"no image with tag {tag} found")

    def image_by_digest(self, digest: str) -> Image:
        results = []
        for image in self.images():
            if image.digest:
                if image.digest == digest:
                    results.append(image)

        if len(results) == 0:
            raise LocalDriverError(f"no image with digest {digest[0:12]} found")
        else:
            return results[0]

    def image_by_id(self, id: str) -> Image:
        results = []
        for image in self.images():
            if image.id:
                if image.id == id:
                    results.append(image)

        if len(results) == 0:
            raise LocalDriverError(f"no image with id {id[0:12]} found")
        else:
            return results[0]

    def _get_tags(self, image_id: str) -> List[str]:
        return self._tag_map()[image_id]

    def _get_arch(self, image_id: str) -> str:
        return self._arch_map()[image_id]

    @lru_cache
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
