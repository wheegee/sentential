import pytest
import json
from sentential.lib.shapes import (
    AwsImageDetail,
    AwsImageDetailImageId,
    AwsImageManifest,
    AwsImageManifestLayer,
)
from tests.helpers import (
    generate_random_sha,
    generate_image_layers,
    generate_image_digest,
    generate_image_manifest,
    generate_manifest_list_manifest,
    generate_image_manifest_list,
)


class TestHelpers:
    def test_generate_random_sha(self):
        assert "sha256:" in generate_random_sha()

    def test_generate_image_layers(self):
        layers = generate_image_layers(2)
        assert all(isinstance(layer, AwsImageManifestLayer) for layer in layers)

    def test_generate_image_digest(self):
        two_layers = generate_image_layers(2)
        assert "sha256:" in generate_image_digest(two_layers)

    def test_generate_image_manifest(self):
        assert isinstance(generate_image_manifest(), AwsImageManifest)

    def test_generate_manifest_list_manifest(self):
        manifest_list_manifest = generate_manifest_list_manifest(
            image_manifest_digest="sha256:1234",
            image_size=23,
            image_architecture="arm64",
            image_os="linux",
        )
        assert manifest_list_manifest.digest == "sha256:1234"
        assert manifest_list_manifest.size == 23
        assert manifest_list_manifest.platform.architecture == "arm64"
        assert manifest_list_manifest.platform.os == "linux"

    def test_generate_image_manifest_list(self):
        amd_image_manifest = generate_image_manifest()
        arm_image_manifest = generate_image_manifest()
        amd_manifest_digest = generate_random_sha()
        arm_manifest_digest = generate_random_sha()
        image_details = [
            AwsImageDetail(
                registryId='123456',
                repositoryName='test',
                imageId=AwsImageDetailImageId(
                    imageDigest=amd_manifest_digest,
                    imageTag="0.0.1-amd64"
                ),
                imageManifest=json.dumps(amd_image_manifest.dict()) # type: ignore
             ),
            AwsImageDetail(
                registryId='123456',
                repositoryName='test',
                imageId=AwsImageDetailImageId(
                    imageDigest=arm_manifest_digest,
                    imageTag="0.0.1-arm64"
                ),
                imageManifest=json.dumps(arm_image_manifest.dict()) # type: ignore
            ),
        ]
        image_manifest_list = generate_image_manifest_list(image_details)
        assert len(image_manifest_list.manifests) == 2
        assert any(dist.platform.architecture == "amd64" for dist in image_manifest_list.manifests)
        assert any(dist.platform.architecture == "arm64" for dist in image_manifest_list.manifests)
        
        for manifest in image_manifest_list.manifests:
            if manifest.platform.architecture == "amd64":
                assert manifest.digest == amd_manifest_digest
            if manifest.platform.architecture == "arm64":
                assert manifest.digest == arm_manifest_digest
            

