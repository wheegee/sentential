from sentential.lib.ontology import Ontology
from sentential.lib.exceptions import AwsDriverError
from sentential.lib.shapes import (
    AwsImageDescriptions,
    AwsImageDetail,
    AwsImageDetails,
    AwsImageManifest,
    AwsManifestList,
    AwsManifestListManifestPlatform,
    Image,
    AwsEcrAuthorizationData,
    AwsEcrAuthorizationToken,
)
from sentential.lib.clients import clients
from typing import Dict, List, Tuple, Union
from functools import lru_cache
import requests


class ECRApi:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology

    @lru_cache
    def api_token(self) -> AwsEcrAuthorizationData:
        response = clients.ecr.get_authorization_token()
        token = AwsEcrAuthorizationToken(**response)
        return token.authorizationData[0]

    def inspect(self, manifest: AwsImageManifest) -> AwsManifestListManifestPlatform:
        response = self._get(
            f"{self.ontology.context.ecr_rest_url}/blobs/{manifest.config.digest}"
        )
        return AwsManifestListManifestPlatform(**response.json())

    def _get(self, url: str, headers={}):
        auth = f"Basic {self.api_token().authorizationToken}"
        headers["Authorization"] = auth
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response


class AwsEcrDriver:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.repo_name = self.ontology.context.repository_name
        self.api = ECRApi(ontology)

    def images(self) -> List[Image]:
        images = []
        for image_id, image_digest in self._image_identifiers():
            images.append(
                Image(
                    id=image_id,
                    digest=self._get_pulled_digest(image_digest),
                    uri=self._get_image_uri(image_digest),
                    tags=self._get_tags(image_digest),
                    versions=self._get_tags(image_digest),
                    arch=self._get_arch(image_digest),
                )
            )
        return images

    def clean(self) -> None:
        image_details = self._image_details()
        manifest_digests = [
            {"imageDigest": detail.imageId.imageDigest} for detail in image_details
        ]
        clients.ecr.batch_delete_image(
            repositoryName=self.ontology.context.repository_name,
            imageIds=manifest_digests,
        )
        self._image_details.cache_clear()

    def image_by_tag(self, tag: str, arch: str = "any") -> Image:
        return self._image_by("tags", tag, arch)

    def image_by_digest(self, digest: str, arch: str = "any") -> Image:
        return self._image_by("digest", digest, arch)

    def image_by_id(self, id: str, arch: str = "any") -> Image:
        return self._image_by("id", id, arch)

    def _image_by(self, attribute: str, value: str, arch: str = "any") -> Image:
        results = []
        images = self.images()

        if arch != "any":
            images = [image for image in images if image.arch == arch]

        for image in self.images():
            attr = getattr(image, attribute)
            if isinstance(attr, list):
                if value in attr:
                    results.append(image)
            elif isinstance(attr, str):
                if value == attr:
                    results.append(image)
            else:
                raise AwsDriverError("unhandled type in image query")

        humanized_value = value.replace("sha256:", "")[0:12]
        if len(results) == 0:
            raise AwsDriverError(
                f"no images found where {attribute} is {humanized_value} and arch is {arch}"
            )
        elif len(results) > 1:
            raise AwsDriverError(
                f"ambiguous match where {attribute} is {humanized_value} and arch is {arch}"
            )
        else:
            return results[0]

    def _image_identifiers(self) -> List[Tuple[str, str]]:
        pairs = []
        for detail in self._image_details():
            if isinstance(detail.imageManifest, AwsImageManifest):
                image_id = detail.imageManifest.config.digest
                image_digest = detail.imageId.imageDigest
                pairs.append((image_id, image_digest))
        return list(set(pairs))

    def _get_image_uri(self, image_digest: str) -> str:
        return self._uri_list()[image_digest]

    def _get_tags(self, image_digest: str) -> List[str]:
        tags = self._tag_list()[image_digest]
        return [tag for tag in tags if tag is not None]

    def _get_arch(self, image_digest: str) -> str:
        return self._arch_list()[image_digest]

    def _get_pulled_digest(self, image_digest: str) -> str:
        return self._digest_list()[image_digest]

    def _uri_list(self) -> Dict[str, str]:
        uri_list = {}
        for detail in self._image_details():
            if isinstance(detail.imageManifest, AwsImageManifest):
                image_uri = f"{self.ontology.context.repository_url}@{detail.imageId.imageDigest}"
                uri_list[detail.imageId.imageDigest] = image_uri
        return uri_list

    def _digest_list(self) -> Dict[str, str]:
        digest_list = {}
        for detail in self._image_details():
            if isinstance(detail.imageManifest, AwsManifestList):
                for manifest in detail.imageManifest.manifests:
                    image_digest = manifest.digest
                    digest_list[image_digest] = detail.imageId.imageDigest

        for detail in self._image_details():
            if isinstance(detail.imageManifest, AwsImageManifest):
                image_digest = detail.imageId.imageDigest
                if image_digest not in digest_list.keys():
                    digest_list[image_digest] = image_digest

        return digest_list

    def _tag_list(self) -> Dict[str, List[Union[str, None]]]:
        tag_list = {}
        for detail in self._image_details():
            if isinstance(detail.imageManifest, AwsImageManifest):
                image_digest = detail.imageId.imageDigest
                tag = detail.imageId.imageTag
                if image_digest in tag_list.keys():
                    tag_list[image_digest].append(tag)
                else:
                    tag_list[image_digest] = [tag]

            if isinstance(detail.imageManifest, AwsManifestList):
                for manifest in detail.imageManifest.manifests:
                    image_digest = manifest.digest
                    tag = detail.imageId.imageTag
                    if image_digest in tag_list.keys():
                        tag_list[image_digest].append(tag)
                    else:
                        tag_list[image_digest] = [tag]

        return tag_list

    def _arch_list(self) -> Dict[str, str]:
        arch_list = {}
        for detail in self._image_details():
            if isinstance(detail.imageManifest, AwsManifestList):
                for manifest in detail.imageManifest.manifests:
                    arch_list[manifest.digest] = manifest.platform.architecture

        for detail in self._image_details():
            if isinstance(detail.imageManifest, AwsImageManifest):
                image_digest = detail.imageId.imageDigest
                if image_digest not in arch_list.keys():
                    inspect = self.api.inspect(detail.imageManifest)
                    arch_list[image_digest] = inspect.architecture

        return arch_list

    @lru_cache
    def _image_details(self) -> List[AwsImageDetail]:
        response = clients.ecr.describe_images(repositoryName=self.repo_name)
        image_desc = AwsImageDescriptions(**response).imageDetails
        if len(image_desc) == 0:
            return []
        filter = [{"imageDigest": image.imageDigest} for image in image_desc]
        response = clients.ecr.batch_get_image(
            repositoryName=self.repo_name, imageIds=filter
        )
        image_details = AwsImageDetails(**response)
        return image_details.images
