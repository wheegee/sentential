from distutils.version import LooseVersion
from functools import lru_cache
from typing import List, Tuple, Union
from rich.table import Table, box
from sentential.lib.clients import clients
from sentential.lib.drivers.local_bridge import LocalBridge
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import (
    ApiGatewayApi,
    ApiGatewayIntegration,
    ApiGatewayRoute,
    AwsFunction,
    AwsFunctionPublicUrl,
    AwsManifestList,
)
from sentential.lib.exceptions import JoineryError, LocalDriverError
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.mounts.aws_event_schedule import AwsEventScheduleMount
from sentential.lib.mounts.aws_api_gateway import AwsApiGatewayMount, deproxify
from sentential.lib.shapes import SNTL_WORKING_IMAGE_TAG
from pydantic import BaseModel
from python_on_whales.components.image.cli_wrapper import Image


class Row(BaseModel):
    build: str
    arch: str
    digest: str
    dist_digests: List[str]
    status: str
    hrefs: List[str]
    mounts: List[str]


class Joinery:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.local_images = LocalImagesDriver(self.ontology)
        self.ecr_images = AwsEcrDriver(self.ontology)
        self.aws_lambda = AwsLambdaDriver(self.ontology)
        self.local_lambda = LocalLambdaDriver(self.ontology)

    def list(self, verbose: bool = False) -> Table:
        cwi = self._cwi()
        published = self._published()
        merged = self._merge(published, cwi)
        drop = ["digest", "dist_digests"]

        columns = list(Row.schema()["properties"].keys())
        if not verbose:
            for column in drop:
                columns.remove(column)

        table = Table(box=box.SIMPLE, *columns)

        for row in merged:
            if verbose:
                table.add_row(*[str(v) for v in row.dict().values()])
            else:
                table.add_row(*[str(v) for v in row.dict(exclude=set(drop)).values()])

        return table

    def _cwi(self) -> Union[Row, None]:
        try:
            row = {}
            cwi = self.local_images.get_image(SNTL_WORKING_IMAGE_TAG)
            row["build"] = "local"
            row["arch"] = cwi.architecture
            row["digest"] = self._humanize_digest(self._extract_digest(cwi))
            row["dist_digests"] = []
            row["status"] = ""
            row["hrefs"] = []
            row["mounts"] = []

            for container in clients.docker.ps(True):
                if cwi.id == container.image:
                    row["status"] = container.state.status.lower()

            if clients.docker.container.exists("sentential-gw"):
                row["hrefs"].append(
                    self._public_url(f"http://localhost:{LocalBridge.config.gw_port}")
                )

            return Row(**row)
        except LocalDriverError:
            return None

    def _published(self) -> List[Row]:
        rows = []
        deployed_function = self._deployed_function()
        deployed_url = self._deployed_url()
        deployed_schedule = self._deployed_schedule()
        deployed_routes = self._deployed_routes()
        for manifest in self.ecr_images._manifest_lists():
            if not isinstance(manifest.imageManifest, AwsManifestList):
                raise JoineryError("expected AwsManifestList object")

            row = {}
            row["build"] = manifest.imageId.imageTag
            row["arch"] = self._extract_arch(manifest.imageManifest)
            row["digest"] = self._humanize_digest(manifest.imageId.imageDigest)
            row["dist_digests"] = self._humanize_digests(
                self._extract_dist_digests(manifest.imageManifest)
            )
            row["status"] = ""
            row["hrefs"] = []
            row["mounts"] = []

            if isinstance(deployed_function, AwsFunction):
                deployed_digest = self._humanize_digest(
                    deployed_function.Configuration.CodeSha256
                )
                if (
                    deployed_digest == row["digest"]
                    or deployed_digest in row["dist_digests"]
                ):
                    row["status"] = deployed_function.Configuration.State.lower()
                    row["hrefs"].append(self._console_web())
                    if isinstance(deployed_url, AwsFunctionPublicUrl):
                        row["hrefs"].append(self._public_url(deployed_url.FunctionUrl))
                    if deployed_schedule is not None:
                        row["mounts"].append(self._console_schedule(deployed_schedule))
                    if len(deployed_routes) > 0:
                        row["mounts"].append(self._console_routes())

            rows.append(Row(**row))  # row yer boat

        return sorted(rows, key=lambda row: LooseVersion(row.build), reverse=True)

    def _merge(self, published: List[Row], cwi: Union[Row, None]) -> List[Row]:
        if cwi:
            matched = False
            for i, manifest in enumerate(published):
                if cwi.digest == manifest.digest:
                    published[i].build = f"[yellow]{published[i].build}[/yellow]"
                    published[i].digest = f"[yellow]{manifest.digest}[/yellow]"
                    matched = True

                for k, dist in enumerate(manifest.dist_digests):
                    if cwi.digest == dist:
                        published[i].build = f"[yellow]{published[i].build}[/yellow]"
                        published[i].dist_digests[k] = f"[yellow]{dist}[/yellow]"
                        matched = True

            if matched:
                cwi.build = f"[yellow]{cwi.build}[/yellow]"
                cwi.digest = f"[yellow]{cwi.digest}[/yellow]"

            published.insert(0, cwi)
            return published
        else:
            return published

    @lru_cache()
    def _deployed_function(self) -> Union[None, AwsFunction]:
        try:
            resp = clients.lmb.get_function(
                FunctionName=self.ontology.context.resource_name
            )
            return AwsFunction(**resp)
        except:
            return None

    @lru_cache()
    def _deployed_url(self) -> Union[None, AwsFunctionPublicUrl]:
        try:
            resp = clients.lmb.get_function_url_config(
                FunctionName=self.ontology.context.resource_name
            )
            return AwsFunctionPublicUrl(**resp)
        except:
            return None

    @lru_cache()
    def _deployed_schedule(self) -> Union[None, str]:
        try:
            return AwsEventScheduleMount(Ontology()).mounts()[0]
        except:
            return None

    @lru_cache()
    def _deployed_routes(
        self,
    ) -> List[Tuple[ApiGatewayApi, ApiGatewayRoute, ApiGatewayIntegration]]:
        return AwsApiGatewayMount(Ontology())._mounts()

    def _public_url(self, url: str) -> str:
        return f"[link={url}]public_url[/link]"

    def _console_web(self) -> str:
        region = self.ontology.context.region
        function = self.ontology.context.resource_name
        url = f"https://{region}.console.aws.amazon.com/lambda/home?region={region}#/functions/{function}"
        return f"[link={url}]console[/link]"

    def _console_schedule(self, schedule: str) -> Union[None, str]:
        region = self.ontology.context.region
        function = self.ontology.context.resource_name
        url = f"https://{region}.console.aws.amazon.com/events/home?region={region}#/eventbus/default/rules/{function}"
        try:
            return f"[link={url}]{schedule}[/link]"
        except:
            return None

    def _console_routes(self) -> Union[None, str]:
        region = self.ontology.context.region
        links = []
        for api, route, integration in self._deployed_routes():
            text = deproxify(route.RouteKey.split(" ")[-1])
            url = f"https://{region}.console.aws.amazon.com/apigateway/main/develop/routes?api={api.ApiId}&integration={integration.IntegrationId}&region={region}&routes={route.RouteId}"
            links.append(f"[link={url}]{text}[/link]")
        if links:
            return ", ".join(links)
        else:
            return None

    def _extract_arch(self, manifest: AwsManifestList) -> str:
        return ", ".join([m.platform.architecture for m in manifest.manifests])

    def _extract_digest(self, image: Image) -> str:
        if image.repo_digests:
            return image.repo_digests[0].split("@")[-1]
        else:
            return ""

    def _extract_dist_digests(self, manifest: AwsManifestList) -> List[str]:
        return [dist.digest for dist in manifest.manifests]

    def _humanize_digest(self, digest: str) -> str:
        return digest.replace("sha256:", "")[0:12]

    def _humanize_digests(self, digests: List[str]) -> List[str]:
        return [d.replace("sha256:", "")[0:12] for d in digests]
