import re
import os
from typing import List, Union
from functools import lru_cache
import semantic_version as semver
import requests
from distutils.version import LooseVersion
from sentential.lib.drivers.spec import ImagesDriver
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.exceptions import AwsDriverError
from sentential.lib.shapes import (
    AwsEcrAuthorizationData,
    AwsEcrAuthorizationToken,
    AwsImageDescriptions,
    AwsImageDetail,
    AwsImageDetails,
    AwsImageManifest,
    AwsManifestList,
    AwsManifestListManifestPlatform,
)


class ECRApi:
    """currently unused, but will be needed soon enough"""

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


class SemVer:
    """encapsulates semver behavior, only used via AwsEcrDriver"""

    def __init__(self, images: List[AwsImageDetail]) -> None:
        self.images = images
        self.regex = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"

    @property
    def versions(self) -> List[str]:
        images = self.images
        versions = []
        for image in images:
            if image.imageId.imageTag:
                versions.append(image.imageId.imageTag)
        return list(set(versions))

    @property
    def semver(self) -> List[str]:
        matcher = re.compile(self.regex)
        versions = self.versions
        versions = [version for version in versions if matcher.match(version)]
        versions = sorted(versions, key=lambda v: LooseVersion(v))
        return versions

    @property
    def latest(self) -> str:
        if self.semver:
            return self.semver[-1]
        else:
            return "0.0.0"

    def next(self, major=False, minor=False) -> str:
        latest = semver.Version(self.latest)
        if major:
            return str(latest.next_major())
        if minor:
            return str(latest.next_minor())
        else:
            return str(latest.next_patch())


class AwsEcrDriver(ImagesDriver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.repo_name = self.ontology.context.repository_name
        self.manifest_list_ref = ontology.context.repository_url.replace("/", "_")

    def get_image(self, tag: Union[str, None] = None) -> AwsImageDetail:
        manifest_lists = self._manifest_lists()

        if tag is None:
            tag = SemVer(manifest_lists).latest

        for manifest in manifest_lists:
            if manifest.imageId.imageTag == tag:
                return manifest

        raise AwsDriverError("no image found for {tag} tag")

    def next(self, major: bool = False, minor: bool = False) -> str:
        return SemVer(self._manifest_lists()).next(major, minor)

    def clean(self) -> None:
        image_details = self._manifests()
        if len(image_details) == 0:
            return
        manifest_digests = [
            {"imageDigest": detail.imageId.imageDigest} for detail in image_details
        ]
        clients.ecr.batch_delete_image(
            repositoryName=self.ontology.context.repository_name,
            imageIds=manifest_digests,
        )
        self._clean_manifests()
        self._manifests.cache_clear()

    def _manifest_lists(self) -> List[AwsImageDetail]:
        manifest_lists = []
        for manifest in self._manifests():
            if isinstance(manifest.imageManifest, AwsManifestList):
                manifest_lists.append(manifest)
        return manifest_lists

    @lru_cache
    def _manifests(self) -> List[AwsImageDetail]:
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

    def _clean_manifests(self) -> None:
        dir = os.path.expanduser("~/.docker/manifests/")
        for manifest in os.listdir(dir):
            if re.search(self.manifest_list_ref, manifest):
                for file in os.listdir(os.path.join(dir, manifest)):
                    os.remove(os.path.join(dir, manifest, file))
                os.rmdir(os.path.join(dir, manifest))
