from sentential.lib.aws import Repository
from sentential.lib.aws import Lambda as AwsLambda
from sentential.lib.const import CWI_TAG
from sentential.lib.local import Lambda as LocalLambda
from sentential.lib.local import Image as LocalImage
from typing import List
import semantic_version as semver
from rich.table import Table
from rich import print


class Ontology:
    def __init__(self):
        self.repo = Repository()

    def semvers(self) -> List[str]:
        return [image.tag for image in self.repo.semver()]

    def latest(self) -> str:
        if self.repo.latest() is None:
            return None
        else:
            return self.repo.latest().tag

    def published(self, sha) -> bool:
        for image in self.repo.semver():
            if image.id == sha:
                return True
        return False

    def next(self, major=False, minor=False) -> str:
        latest = "0.0.0" if self.latest() is None else self.latest()
        latest = semver.Version(latest)
        if major:
            return latest.next_major()
        if minor:
            return latest.next_minor()
        else:
            return latest.next_patch()

    def print(self) -> Table:
        table = Table("sha", "tag", "arch", "deployed")
        aws_deployed = AwsLambda.deployed()
        local_deployed = LocalLambda.deployed()
        current_working_image = LocalImage(CWI_TAG)

        data = {}
        images = self.repo.semver()
        if current_working_image.exists:
            images.append(current_working_image)

        for image in images:
            data[image.id] = {"tag": [], "arch": [], "deployed": []}

        for image in images:
            data[image.id]["tag"].append(image.tag)
            data[image.id]["arch"].append(image.arch)
            if aws_deployed != None and aws_deployed.image.id == image.id:
                data[image.id]["deployed"].append("aws")
            if local_deployed != None and local_deployed.image.id == image.id:
                data[image.id]["deployed"].append("local")

        for sha, data in data.items():
            table.add_row(sha, *[str(list(set(value))) for value in data.values()])

        print(table)
