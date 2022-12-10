import in_place
from rich.table import Table
from typing import Any, List
import hashlib
import random


def table_headers(table: Table) -> List[str]:
    return [str(column.header) for column in table.columns]


def table_body(table: Table) -> List[List[Any]]:
    cells = [column._cells for column in table.columns]
    body = [list(row) for row in zip(*cells)]
    return body


def rewrite(file: str, target: str, replace: str) -> None:
    with in_place.InPlace(file) as fp:
        for line in fp:
            if target in line:
                fp.write(replace)


# ECR Mock Data
def generate_random_sha():
    sha = hashlib.sha256(f"{random.randint(0,100)}".encode("utf-8")).hexdigest()
    return f"sha256:{sha}"


def generate_image_layers(n):
    layers = []
    for _ in range(n):
        layers.append(
            {
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                "size": random.randint(100, 1000),
                "digest": generate_random_sha(),
            }
        )
    return layers


def generate_image_digest(layers):
    layer_digests = "".join([layer["digest"] for layer in layers])
    sum_digest = hashlib.sha256(f"{layer_digests}".encode("utf-8")).hexdigest()
    return f"sha256:{sum_digest}"


def generate_image_manifest(config_digest=None):
    layers = generate_image_layers(random.randint(5, 15))
    if config_digest is None:
        config_digest = generate_image_digest(layers)
    return {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": sum([layer["size"] for layer in layers]),
            "digest": config_digest,
        },
        "layers": layers,
    }


def generate_manifest_list_distribution(
    image_manifest: dict, architecture: str = "amd64", os: str = "linux"
):
    return {
        "mediaType": image_manifest["config"]["mediaType"],
        "digest": image_manifest["config"]["digest"],
        "size": image_manifest["config"]["size"],
        "platform": {"architecture": architecture, "os": os},
    }


def generate_image_manifest_list():
    arm_image_manifest = generate_image_manifest()
    amd_image_manifest = generate_image_manifest()
    arm_distribution = generate_manifest_list_distribution(
        arm_image_manifest, architecture="arm64"
    )
    amd_distribution = generate_manifest_list_distribution(
        amd_image_manifest, architecture="amd64"
    )
    manifest_list = {
        "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
        "schemaVersion": 2,
        "manifests": [arm_distribution, amd_distribution],
    }

    return {
        "image_manifests": [arm_image_manifest, amd_image_manifest],
        "manifest_list": manifest_list,
    }
