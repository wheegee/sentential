from rich.table import Table
from typing import Any, List, Union
import hashlib
import random
import fileinput
from ast import literal_eval
from sentential.lib.shapes import (
    AwsImageDetail,
    AwsImageManifest,
    AwsImageManifestLayer,
    AwsManifestList,
    AwsManifestListDistribution,
    AwsManifestListManifestPlatform,
)


class MockException(BaseException):
    pass


def table_headers(table: Table) -> List[str]:
    return [str(column.header) for column in table.columns]


def table_body(table: Table) -> List[List[Any]]:
    cells = [column._cells for column in table.columns]
    body = [list(row) for row in zip(*cells)]
    for i, row in enumerate(body):
        for j, column in enumerate(row):
            if str(column).startswith("[") and str(column).endswith("]"):
                body[i][j] = literal_eval(str(column))
            if str(column) == "None":
                body[i][j] = literal_eval(str(column))

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


def generate_image_layers(n) -> List[AwsImageManifestLayer]:
    layers = []
    for _ in range(n):
        layers.append(
            AwsImageManifestLayer(
                size=random.randint(100, 1000), digest=generate_random_sha()
            )
        )
    return layers


def generate_image_digest(layers: List[AwsImageManifestLayer]) -> str:
    layer_digests = "".join([layer.digest for layer in layers])
    sum_digest = hashlib.sha256(f"{layer_digests}".encode("utf-8")).hexdigest()
    return f"sha256:{sum_digest}"


def generate_image_manifest(config_digest: Union[str, None] = None) -> AwsImageManifest:
    layers = generate_image_layers(random.randint(5, 15))
    if config_digest is None:
        config_digest = generate_image_digest(layers)

    return AwsImageManifest(
        config=AwsImageManifestLayer(
            size=sum([layer.size for layer in layers]), digest=config_digest
        ),
        layers=layers,
    )


def generate_manifest_list_manifest(
    image_manifest_digest: str,
    image_size: int,
    image_architecture: str = "amd64",
    image_os: str = "linux",
) -> AwsManifestListDistribution:
    return AwsManifestListDistribution(
        digest=image_manifest_digest,
        size=image_size,
        platform=AwsManifestListManifestPlatform(
            os=image_os, architecture=image_architecture
        ),
    )


def generate_image_manifest_list(
    image_details: List[AwsImageDetail],
) -> AwsManifestList:
    distributions = []
    for image_detail in image_details:
        tag = image_detail.imageId.imageTag

        if tag is None:
            raise MockException("image must have tag for mock generation")

        if "arm64" not in tag and "amd64" not in tag:
            raise MockException("image tag must include arch for mock generation")

        if "arm64" in tag:
            arch = "arm64"

        if "amd64" in tag:
            arch = "amd64"

        distributions.append(
            generate_manifest_list_manifest(
                image_manifest_digest=image_detail.imageId.imageDigest,
                image_size=image_detail.imageManifest.config.size,
                image_architecture=arch,
                image_os="linux",
            )
        )

    return AwsManifestList(manifests=distributions)
