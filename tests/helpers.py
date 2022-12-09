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
    return hashlib.sha256(f"{random.randint(0,100)}".encode("utf-8")).hexdigest()

def generate_image_layers(n):
    layers = []
    for _ in range(n):
        layers.append(
            {
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                "size": random.randint(100, 1000),
                "digest": f"sha256:{generate_random_sha()}",
            }
        )
    return layers

def generate_image_digest(layers):
    layer_digests = "".join([layer["digest"] for layer in layers])
    return hashlib.sha256(f"{layer_digests}".encode("utf-8")).hexdigest()

def generate_image_manifest(image_digest=None):
    layers = generate_image_layers(random.randint(5,15))
    if image_digest is None:
        image_digest = generate_image_digest(layers)
    return {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": sum([layer["size"] for layer in layers]),
            "digest": image_digest,
        },
        "layers": layers,
    }