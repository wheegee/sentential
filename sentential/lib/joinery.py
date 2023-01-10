from distutils.version import LooseVersion
from typing import List, Union
from rich.table import Table, box
from sentential.lib.clients import clients
from sentential.lib.drivers.local_bridge import LocalBridge
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import (
    AwsManifestList,
)
from sentential.lib.exceptions import JoineryError, LocalDriverError
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver

from rich.panel import Panel
from rich import print

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

    def _get_local_row(self) -> Union[None, List[str]]:
        try:
            cwi = self.local_images.get_image("cwi")
            tag = "cwi"
            arch = cwi.architecture
            digest = ""
            status = ""
            href = ""

            if cwi.repo_digests:
                digest = cwi.repo_digests[0].split("@")[-1].replace("sha256:", "")[0:12]

            for container in clients.docker.ps(True):
                if container.image == cwi.id:
                    status = container.state.status
            
            if self.local_lambda.deployed_public_url():
                href = self._to_hyperlink(LocalBridge.config.gw_port, "public_url")

            return [tag, arch, digest, status, href] # type: ignore
        except LocalDriverError:
            return None

    def _get_aws_rows(self) -> List[str]:
        deployed = self.aws_lambda.deployed_function()
        public_url = self.aws_lambda.deployed_public_url()
        rows = []
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

            rows.append([tag, arch, manifest_list_digest[0:12], status, ", ".join(hrefs)])

        return sorted(rows, key=lambda row: LooseVersion(row[0]), reverse=True)

    def list(self) -> Table:
        table = Table(box=box.SIMPLE, *["tag", "arch", "digest", "status", "hrefs"])
        local = self._get_local_row()
        aws = self._get_aws_rows()

        if local:
            table.add_row(*local)

        for row in aws:
            table.add_row(*row)

        return table
