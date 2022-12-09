from operator import concat
from typing import Dict, List
from rich.table import Table, box
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.exceptions import JoineryError
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Image, ImageView


class Joinery:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.docker = LocalImagesDriver(self.ontology)
        self.ecr = AwsEcrDriver(self.ontology)

    def group_by_id(self) -> Dict[str, List[Image]]:
        local_images = [image for image in self.docker.images()]
        aws_images = [image for image in self.ecr.images()]
        by_id = {}
        for image in local_images + aws_images:
            if image.id in by_id:
                by_id[image.id].append(image)
            else:
                by_id[image.id] = [image]
        return by_id

    def merge_on_id(self) -> List[ImageView]:
        merged = []

        for id, images in self.group_by_id().items():
            digest = None
            tags = []
            versions = []
            uri = None
            arch = None
            for image in images:
                if image.digest is not None:
                    digest = image.digest

                if image.tags:
                    tags = concat(tags, image.tags)

                if image.versions:
                    versions = concat(versions, image.versions)

                if image.uri:
                    uri = image.uri

                if arch is None:
                    arch = image.arch
                else:
                    if arch != image.arch:
                        raise JoineryError(
                            f"found two differing architectures for the same image id {image.id}"
                        )

            merged.append(
                ImageView(
                    id=id,
                    digest=digest,
                    uri=uri,
                    tags=list(tags),
                    versions=list(versions),
                    arch=arch,  # type: ignore
                )
            )

        return merged

    def list(self, drop: List[str] = []) -> Table:
        columns = list((ImageView.__fields__.keys()))

        for header in drop:
            if header in columns:
                columns.remove(header)

        data = [list(i.dict(exclude=set(drop)).values()) for i in self.merge_on_id()]
        table = Table(box=box.SIMPLE, *columns)
        for row in data:
            table.add_row(*[str(value) for value in row])
        return table
