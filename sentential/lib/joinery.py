from distutils.version import LooseVersion
from typing import Any, List, Union
from rich.table import Table, box
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import (
    AwsManifestList,
)
from sentential.lib.exceptions import JoineryError, LocalDriverError
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

    def _get_aws_rows(self, cwi_digest: str = "") -> List[List[str]]:
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

            manifest_list_digest = manifest.imageId.imageDigest.replace("sha256:", "")[
                0:12
            ]
            image_digests = [
                dist.digest.replace("sha256:", "")[0:12]
                for dist in manifest.imageManifest.manifests
            ]

            hrefs = []
            status = ""
            cwi = "false"
            if deployed and deployed.CodeSha256[0:12] in image_digests:
                status = deployed.State.lower()
                hrefs = [self._webconsole_hyperlink()]
                if public_url:
                    hrefs.append(
                        self._to_hyperlink(public_url.FunctionUrl, "public_url")
                    )

                if cwi_digest:
                    if cwi_digest == manifest_list_digest:
                        cwi = "true"
                    if cwi_digest in image_digests:
                        cwi = "true"

            rows.append(
                [cwi, tag, arch, manifest_list_digest, status, ", ".join(hrefs)]
            )

        return sorted(rows, key=lambda row: LooseVersion(row[0]), reverse=True)

    def _get_cwi_row(self) -> Union[None, List[str]]:
        try:
            cwc = self.local_lambda.deployed_function()
            if cwc:
                cwi = clients.docker.image.inspect(cwc.image)
            else:
                cwi = self.local_images.get_image("cwi")

            url = self.local_lambda.deployed_public_url()
            arch = cwi.architecture
            digest = ""
            status = ""
            hrefs = ""

            if cwi.repo_digests:
                digest = cwi.repo_digests[0].split("@")[-1].replace("sha256:", "")[0:12]

            if cwc and cwc.image == cwi.id:
                if cwc.state.status:
                    status = cwc.state.status

            if url:
                hrefs = self._to_hyperlink(url, "public_url")

            return ["true", "local", arch, digest, status, hrefs]

        except LocalDriverError:
            return None

    def _highlight(self, rows):
        for i, row in enumerate(rows):
            if row[0] == "true":
                rows[i][1] = f"[yellow]{rows[i][1]}[/yellow]"

    def list(self) -> Table:
        columns = ["build", "arch", "digest", "status", "hrefs"]
        table = Table(box=box.SIMPLE, *columns)
        cwi_row = self._get_cwi_row()

        if cwi_row:
            rows = self._get_aws_rows(cwi_row[3])
            rows.insert(0, cwi_row)
        else:
            rows = self._get_aws_rows()

        self._highlight(rows)

        for row in rows:
            table.add_row(*row[1:])

        return table
