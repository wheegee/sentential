import json
from os import makedirs, rmdir, listdir
from typing import List, cast

from pydantic import BaseModel
from sentential.lib.shapes import (
    AwsImageDetails,
    AwsImageManifest,
    AwsManifestList,
    AwsManifestListManifestPlatform,
)
from sentential.lib.clients import clients
from tests.helpers import generate_image_manifest, generate_manifest_list_manifest, MockException

#
# Docker Client Mockery
#

# from pytest import MonkeyPatch
# from sentential.lib.clients import clients
# monkeypatch = MonkeyPatch()
# monkeypatch.setattr(clients.docker, 'push', push_mock)
# monkeypatch.setattr(clients.docker.manifest, "create", manifest_create_mock)
# monkeypatch.setattr(clients.docker.manifest, 'push', manifest_push_mock)


class DockerManifestDescriptor(BaseModel):
    mediaType: str
    digest: str
    size: int
    platform: AwsManifestListManifestPlatform
    SchemaV2Manifest: AwsImageManifest


class DockerManifest(BaseModel):
    Ref: str
    Descriptor: DockerManifestDescriptor


def push_mock(tag: str):
    image_id = clients.docker.image.inspect(tag).id
    image_tag = tag.split("/")[1].split(":")[-1]
    repo_name = tag.split("/")[1].split(":")[0]
    image_manifest = generate_image_manifest(image_id)
    clients.ecr.put_image(
        repositoryName=repo_name,
        imageManifest=json.dumps(image_manifest.dict()),
        imageTag=image_tag,
    )


def manifest_create_mock(manifest_list_uri: str, image_manifest_uris: List[str], *args):
    registry_url = manifest_list_uri.split("/")[0]
    repo_name = manifest_list_uri.split("/")[1].split(":")[0]
    manifest_list_tag = manifest_list_uri.split("/")[1].split(":")[-1]

    image_manifest_tags = [
        uri.split("/")[1].split(":")[-1] for uri in image_manifest_uris
    ]
    manifest_list_dir = f".docker/{registry_url}_{repo_name}-{manifest_list_tag}"

    makedirs(manifest_list_dir, exist_ok=True)

    image_ids = [{"imageTag": tag} for tag in image_manifest_tags]
    detail = AwsImageDetails(
        **clients.ecr.batch_get_image(repositoryName=repo_name, imageIds=image_ids)
    )

    for image in detail.images:
        if not isinstance(image.imageManifest, AwsImageManifest):
            raise MockException("manifest create mock given wrong image type")

        image_manifest_uri = (
            f"{registry_url}/{image.repositoryName}:{image.imageId.imageTag}"
        )
        image_manifest_file = (
            f"{registry_url}_{image.repositoryName}-{image.imageId.imageTag}"
        )
        inspect = clients.docker.image.inspect(image.imageManifest.config.digest)

        with open(f"{manifest_list_dir}/{image_manifest_file}", "w") as fp:
            docker_manifest = DockerManifest(
                Ref=image_manifest_uri,
                Descriptor=DockerManifestDescriptor(
                    mediaType=image.imageManifest.mediaType,
                    digest=image.imageId.imageDigest,
                    size=image.imageManifest.config.size,
                    platform=AwsManifestListManifestPlatform(
                        os=inspect.os, architecture=inspect.architecture
                    ),
                    SchemaV2Manifest=image.imageManifest,
                ),
            )
            json.dump(docker_manifest.dict(), fp)


def manifest_push_mock(manifest_list_uri: str, purge: bool):
    registry_url = manifest_list_uri.split("/")[0]
    manifest_list_tag = manifest_list_uri.split("/")[1].split(":")[-1]
    repo_name = manifest_list_uri.split("/")[1].split(":")[0]
    manifest_list_dir = f".docker/{registry_url}_{repo_name}-{manifest_list_tag}"

    image_distributions = []
    for image_manifest_file in listdir(manifest_list_dir):
        with open(f"{manifest_list_dir}/{image_manifest_file}") as json_manifest:
            docker_manifest = DockerManifest(**json.load(json_manifest))
            manifest_digest = docker_manifest.Descriptor.digest
            size = docker_manifest.Descriptor.size
            os = docker_manifest.Descriptor.platform.os
            arch = docker_manifest.Descriptor.platform.architecture
            image_distributions.append(
                generate_manifest_list_manifest(manifest_digest, size, arch, os)
            )

    manifest_list = AwsManifestList(manifests=image_distributions)

    clients.ecr.put_image(
        repositoryName=repo_name,
        imageManifest=json.dumps(manifest_list.dict()),
        imageTag=manifest_list_tag,
    )

    if purge:
        rmdir(manifest_list_dir)
