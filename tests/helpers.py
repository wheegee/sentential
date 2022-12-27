from rich.table import Table
from typing import Any, List
import hashlib
import random
import fileinput


def table_headers(table: Table) -> List[str]:
    return [str(column.header) for column in table.columns]


def table_body(table: Table) -> List[List[Any]]:
    cells = [column._cells for column in table.columns]
    body = [list(row) for row in zip(*cells)]
    return body


def rewrite(file: str, target: str, replace: str) -> None:
    with fileinput.FileInput(file, inplace=True) as f:
        for line in f:
            if target in line:
                print(replace, end="\n")
            else:
                print(line, end="")


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
    manifest_digest: str, size: int, architecture: str = "amd64", os: str = "linux"
):
    return {
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "digest": manifest_digest,
        "size": size,
        "platform": {"architecture": architecture, "os": os},
    }


def generate_image_manifest_list():
    arm_image_manifest = generate_image_manifest()
    amd_image_manifest = generate_image_manifest()
    arm_distribution = generate_manifest_list_distribution(
        generate_random_sha(),
        arm_image_manifest["config"]["size"],
        architecture="arm64",
    )
    amd_distribution = generate_manifest_list_distribution(
        generate_random_sha(),
        amd_image_manifest["config"]["size"],
        architecture="amd64",
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
