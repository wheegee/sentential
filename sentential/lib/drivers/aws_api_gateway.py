from sentential.lib.exceptions import ApiGatewayResourceNotFound
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import (
    Function,
    ApiGatewayDomain,
    ApiGatewayIntegration,
    ApiGatewayMapping,
    ApiGatewayParsedUrl,
    ApiGatewayRoute,
)

from furl import furl
from typing import List
from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    normalized_url = "/".join(furl(url).path.normalize().segments)
    return normalized_url


def normalize_route(url: str) -> str:
    normalized_route = furl(url).path.normalize()
    decoded = "/".join(normalized_route.segments)
    return f"/{decoded}"


class AwsApiGatewayDriver:
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.context = self.ontology.context
        self.account_id = self.context.account_id
        self.partition = self.context.partition
        self.region = self.context.region
        self.repo_name = self.context.repository_name
        self.statement_id = f"{self.partition}-{self.region}-{self.repo_name}"

    @classmethod
    def sentential_domains(cls) -> List[ApiGatewayDomain]:
        sentential_domains = []
        for domain in clients.api_gw.get_domain_names()["Items"]:
            domain = ApiGatewayDomain(**domain)
            if "sentential" in domain.Tags.keys():
                sentential_domains.append(domain)
        return sentential_domains

    @classmethod
    def domains(cls) -> List[ApiGatewayDomain]:
        domains = cls.sentential_domains()
        for domain in domains:
            for mapping in clients.api_gw.get_api_mappings(
                DomainName=domain.DomainName
            )["Items"]:
                mapping = ApiGatewayMapping(**mapping)
                domain.Mappings.append(mapping)
                for route in clients.api_gw.get_routes(ApiId=mapping.ApiId)["Items"]:
                    route = ApiGatewayRoute(**route)
                    mapping.Routes.append(route)
                    if route.Target:
                        integration_id = route.Target.split("/")[-1]
                        integration = clients.api_gw.get_integration(
                            ApiId=mapping.ApiId, IntegrationId=integration_id
                        )
                        route.Integration = ApiGatewayIntegration(**integration)
        return domains

    @classmethod
    def autocomplete(cls) -> List[str]:
        urls = []
        for domain in cls.domains():
            urls.append(normalize_url(domain.DomainName))
            for mapping in domain.Mappings:
                for route in mapping.Routes:
                    uri = route.RouteKey.split(" ")[-1]
                    full_path = normalize_url(
                        f"{domain.DomainName}/{mapping.ApiMappingKey}/{uri}"
                    )
                    urls.append(str(full_path))
        if len(urls) == 0:
            return ["no discoverable api gateway endpoints (just link to docs)"]
        return list(set(urls))

    def parse(self, url: str) -> ApiGatewayParsedUrl:
        parsed = urlparse(f"https://{url}")
        domains = self.domains()
        for domain in domains:
            if domain.DomainName == parsed.netloc:
                # if matching route exists under mapping, return it
                for mapping in domain.Mappings:
                    for route in mapping.Routes:
                        existant_verb, existant_mount = route.RouteKey.split(" ")
                        found_path = normalize_route(
                            f"/{mapping.ApiMappingKey}/{existant_mount}"
                        )
                        if parsed.path == found_path:
                            full_path = normalize_url(
                                f"{domain.DomainName}/{found_path}"
                            )
                            return ApiGatewayParsedUrl(
                                ApiId=mapping.ApiId,
                                ApiMappingId=mapping.ApiMappingId,
                                ApiMappingKey=mapping.ApiMappingKey,
                                RouteId=route.RouteId,
                                RouteKey=route.RouteKey,
                                Route=str(
                                    furl(existant_mount)
                                    .path.remove("/{proxy+}")
                                    .remove("/{proxy}")
                                ),
                                Verb=existant_verb,
                                FullPath=str(full_path),
                            )

                # else return new path under matching mapping
                # sort so that "startswith" conditional matches against longest to shortest possibilities
                domain.Mappings.sort(key=lambda m: len(m.ApiMappingKey), reverse=True)
                for mapping in domain.Mappings:
                    map_key_path = f"/{mapping.ApiMappingKey}"
                    if parsed.path.startswith(map_key_path):
                        full_path = normalize_url(f"{domain.DomainName}/{parsed.path}")
                        route_key = normalize_route(
                            parsed.path.replace(map_key_path, "", 1)
                        )
                        return ApiGatewayParsedUrl(
                            ApiId=mapping.ApiId,
                            ApiMappingId=mapping.ApiMappingId,
                            ApiMappingKey=mapping.ApiMappingKey,
                            RouteId=None,
                            RouteKey=f"ANY {route_key}",
                            Route=str(
                                furl(route_key)
                                .path.remove("/{proxy+}")
                                .remove("/{proxy}")
                            ),
                            FullPath=str(full_path),
                        )

        # else explode
        raise ApiGatewayResourceNotFound(
            f"invalid url ({url}): bad formatting, or attempting to mount to non-existant domain/mapping"
        )

    def _ensure_integration(
        self, parsed_url: ApiGatewayParsedUrl, function: Function
    ) -> ApiGatewayIntegration:
        desired_integration = ApiGatewayIntegration(
            IntegrationUri=function.arn,
            RequestParameters={
                "overwrite:path": "/$request.path.proxy",
                "overwrite:header.X-Forwarded-Prefix": parsed_url.Route,
            },
        )

        # if the desired integration already exists, return it
        for integration in clients.api_gw.get_integrations(ApiId=parsed_url.ApiId)[
            "Items"
        ]:
            current_integration = ApiGatewayIntegration(**integration)
            if current_integration.IntegrationId is not None:
                current_integration.IntegrationId = None
                if desired_integration == current_integration:
                    response = clients.api_gw.get_integration(
                        ApiId=parsed_url.ApiId,
                        IntegrationId=integration["IntegrationId"],
                    )
                    return ApiGatewayIntegration(**response)

        # else create the desired integration and return it
        desired_integration = desired_integration.dict(exclude={"IntegrationId"})
        desired_integration["ApiId"] = parsed_url.ApiId
        response = clients.api_gw.create_integration(**desired_integration)
        return ApiGatewayIntegration(**response)

    def _ensure_route(
        self, parsed_url: ApiGatewayParsedUrl, integration: ApiGatewayIntegration
    ) -> ApiGatewayRoute:
        target = f"integrations/{integration.IntegrationId}"
        try:
            response = clients.api_gw.create_route(
                ApiId=parsed_url.ApiId,
                RouteKey=parsed_url.RouteKey,
                Target=target,
            )
        except clients.api_gw.exceptions.ConflictException:
            response = clients.api_gw.update_route(
                ApiId=parsed_url.ApiId,
                RouteId=parsed_url.RouteId,
                RouteKey=parsed_url.RouteKey,
                Target=target,
            )
        return ApiGatewayRoute(**response)

    def _ensure_permission(self, parsed_url: ApiGatewayParsedUrl, function: Function):
        verb, route = parsed_url.RouteKey.split(" ")
        try:
            clients.lmb.remove_permission(
                FunctionName=function.name,
                StatementId=self.statement_id,
            )
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass

        response = clients.lmb.add_permission(
            FunctionName=function.arn,
            StatementId=self.statement_id,
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{self.region}:{self.account_id}:{parsed_url.ApiId}/*/*/{{proxy+}}",
        )
        return response

    def put_route(self, url: str, function: Function) -> ApiGatewayRoute:
        parsed_url = self.parse(url)
        integration = self._ensure_integration(parsed_url, function)
        route = self._ensure_route(parsed_url, integration)
        permission = self._ensure_permission(parsed_url, function)
        return route

    def delete_routes(self, function: Function) -> None:
        domains = self.domains()
        to_delete = []
        for domain in domains:
            for mapping in domain.Mappings:
                for route in mapping.Routes:
                    if route.Integration:
                        if route.Integration.IntegrationUri == function.arn:
                            to_delete.append([mapping, route])

        for mapping, route in to_delete:
            try:
                clients.api_gw.delete_route(ApiId=mapping.ApiId, RouteId=route.RouteId)
            except clients.api_gw.exceptions.NotFoundException:
                pass

        for mapping, route in to_delete:
            try:
                clients.api_gw.delete_integration(
                    ApiId=mapping.ApiId,
                    IntegrationId=route.Integration.IntegrationId,
                )
            except clients.api_gw.exceptions.NotFoundException:
                pass
