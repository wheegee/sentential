from typing import List
import pytest
from sentential.lib.shapes import AwsImageManifest, AwsImageManifestLayer, AwsManifestList
from tests.helpers import generate_random_sha, generate_image_layers, generate_image_digest, generate_image_manifest, generate_manifest_list_manifest, generate_image_manifest_list

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
            image_manifest_digest = "sha256:1234",
            image_size = 23,
            image_architecture = "arm64",
            image_os = "linux",
        )
        assert manifest_list_manifest.digest == "sha256:1234"
        assert manifest_list_manifest.size == 23
        assert manifest_list_manifest.platform.architecture == "arm64"
        assert manifest_list_manifest.platform.os == "linux"

    def test_generate_image_manifest_list(self):
        image_manifest_list = generate_image_manifest_list()
        assert "image_manifests" in image_manifest_list
        assert "manifest_list" in image_manifest_list
        assert all(isinstance(image, AwsImageManifest) for image in image_manifest_list["image_manifests"])
        assert isinstance(image_manifest_list["manifest_list"], AwsManifestList)