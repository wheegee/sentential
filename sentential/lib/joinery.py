from rich.table import Table, box
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import AwsManifestList
from sentential.lib.exceptions import JoineryError
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.drivers.local_images import LocalImagesDriver


class Joinery:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.local_images = LocalImagesDriver(self.ontology)
        self.ecr_images = AwsEcrDriver(self.ontology)

    def list(self) -> Table:
        table = Table(box=box.SIMPLE, *["tag", "arch", "digest"])
        for manifest in self.ecr_images._manifest_lists():
            if not isinstance(manifest.imageManifest, AwsManifestList):
                raise JoineryError(
                    f"joinery recieved something that isn't a manifest list"
                )

            tag = manifest.imageId.imageTag
            arch = ", ".join(
                [
                    dist.platform.architecture
                    for dist in manifest.imageManifest.manifests
                ]
            )
            digest = manifest.imageId.imageDigest.replace("sha256:", "")[0:12]
            table.add_row(*[tag, arch, digest])

        return table
