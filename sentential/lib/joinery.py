from operator import concat
from typing import Dict, List
from rich.table import Table, box
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Image, ImageView


class Joinery:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.local = LocalLambdaDriver(self.ontology)
        self.aws = AwsLambdaDriver(self.ontology)
        try:
            self.local_deployment = self.local.deployed()
        except:
            self.local_deployment = None

        try:
            self.aws_deployment = self.aws.deployed()
        except:
            self.aws_deployment = None

    def group_by_id(self) -> Dict[str, List[Image]]:
        local_images = [image for image in self.local.images()]
        aws_images = [image for image in self.aws.images()]
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
            href = []
            for image in images:
                if image.digest is not None:
                    digest = image.digest

                if image.tags:
                    tags = concat(tags, image.tags)

                if image.versions:
                    versions = concat(versions, image.versions)

                if self.local_deployment:
                    if self.local_deployment.image.id == image.id:
                        public_url = self.local_deployment.public_url
                        if public_url:
                            href.append(f"[link={public_url}]local_url[/link]")

                if self.aws_deployment:
                    if self.aws_deployment.image.id == image.id:
                        web_console_url = self.aws_deployment.web_console_url
                        public_url = self.aws_deployment.public_url
                        if web_console_url:
                            href.append(f"[link={web_console_url}]aws_console[/link]")
                        if public_url:
                            href.append(f"[link={public_url}]public_url[/link]")

            merged.append(
                ImageView(
                    id=id,
                    digest=digest,
                    tags=list(tags),
                    versions=list(versions),
                    href=href,
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
