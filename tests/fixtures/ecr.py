import pytest
import json
import hashlib
import random
from typing import List, Dict
from sentential.lib.ontology import Ontology
from sentential.lib.clients import clients


@pytest.fixture(scope="class")
def ecr_images(ontology: Ontology):
    IMAGES = ["0.0.1", "0.0.2", "0.1.0", "0.1.1", "1.0.0"]

    try:
        clients.ecr.delete_repository(
            repositoryName=ontology.context.repository_name,
            force=True,
        )
    except clients.ecr.exceptions.RepositoryNotFoundException:
        pass

    clients.ecr.create_repository(repositoryName=ontology.context.repository_name)

    def generate_random_digest() -> str:
        digest = hashlib.sha256(
            str(random.randint(0, 1000)).encode("utf-8")
        ).hexdigest()
        return f"sha256:{digest}"

    def generate_layers(num) -> List[Dict]:
        layers = []
        for _ in range(num):
            layers.append(
                {
                    "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                    "size": random.randint(10, 100),
                    "digest": generate_random_digest(),
                }
            )
        return layers

    def generate_config() -> Dict:
        return {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": random.randint(50, 1000),
            "digest": generate_random_digest(),
        }

    for semver in IMAGES:
        clients.ecr.put_image(
            repositoryName=ontology.context.repository_name,
            imageManifest=json.dumps(
                {
                    "schemaVersion": 2,
                    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                    "config": generate_config(),
                    "layers": generate_layers(random.randint(5, 15)),
                }
            ),
            imageManifestMediaType="application/vnd.docker.distribution.manifest.v2+json",
            imageTag=semver,
        )

    yield

    clients.ecr.delete_repository(
        repositoryName=ontology.context.repository_name,
        force=True,
    )
