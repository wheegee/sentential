from sentential.lib.ontology import Ontology
from sentential.lib.shapes import (
    AwsImageDescriptions,
    AwsImageDetail,
    AwsImageDetailImageId,
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


class AwsECRDriver:
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
                    digest=image_digest,
                    tags=self._get_tags(image_digest),
                    versions=self._get_tags(image_digest),
                    arch=self._get_arch(image_digest),
                )
            )
        return images

    @lru_cache
    def _image_details(self) -> List[AwsImageDetail]:
        response = clients.ecr.describe_images(repositoryName=self.repo_name)
        image_desc = AwsImageDescriptions(**response).imageDetails
        filter = [{"imageDigest": image.imageDigest} for image in image_desc]
        response = clients.ecr.batch_get_image(
            repositoryName=self.repo_name, imageIds=filter
        )
        image_details = AwsImageDetails(**response)
        return image_details.images

    def _image_identifiers(self) -> List[Tuple[str, str]]:
        pairs = []
        for detail in self._image_details():
            if isinstance(detail.imageManifest, AwsImageManifest):
                image_id = detail.imageManifest.config.digest
                image_digest = detail.imageId.imageDigest
                pairs.append((image_id, image_digest))
        return list(set(pairs))

    def _get_tags(self, image_digest: str) -> List[str]:
        tags = self._tag_list()[image_digest]
        return [tag for tag in tags if tag is not None]

    def _get_arch(self, image_digest: str) -> str:
        return self._arch_list()[image_digest]

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

    @lru_cache
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
