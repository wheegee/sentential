from rich.table import Table, box
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import (
    AwsManifestList,
)
from sentential.lib.exceptions import JoineryError
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver


class Joinery:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.local_images = LocalImagesDriver(self.ontology)
        self.ecr_images = AwsEcrDriver(self.ontology)
        self.aws_lambda = AwsLambdaDriver(self.ontology)
        self.local_lambda = LocalLambdaDriver(self.ontology)

    def _to_hyperlink(self, url: str, text: str) -> str:
        return f"[link={url}]{text}[/link]"

    def _webconsole_hyperlink(self) -> str:
        region = self.ontology.context.region
        function = self.ontology.context.resource_name
        url = f"https://{region}.console.aws.amazon.com/lambda/home?region={region}#/functions/{function}"
        return self._to_hyperlink(url, "console")

    def list(self) -> Table:
        table = Table(box=box.SIMPLE, *["tag", "arch", "digest", "status", "hrefs"])
        deployed = self.aws_lambda.deployed_function()
        public_url = self.aws_lambda.deployed_public_url()

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

            manifest_list_digest = manifest.imageId.imageDigest.replace("sha256:", "")

            image_digests = [dist.digest for dist in manifest.imageManifest.manifests]

            if deployed and f"sha256:{deployed.CodeSha256}" in image_digests:
                status = deployed.State.lower()
                hrefs = [self._webconsole_hyperlink()]
                if public_url:
                    hrefs.append(
                        self._to_hyperlink(public_url.FunctionUrl, "public_url")
                    )
            else:
                status = ""
                hrefs = ""

            table.add_row(
                *[tag, arch, manifest_list_digest[0:12], status, ", ".join(hrefs)]
            )

        return table
