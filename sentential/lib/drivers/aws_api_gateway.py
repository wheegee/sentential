from sentential.lib.drivers.spec import MountDriver
from sentential.lib.exceptions import MountError
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import (
    ApiGatewayDomains,
    ApiGatewayIntegrations,
    ApiGatewayMappings,
    ApiGatewayRoutes,
    Function,
    ApiGatewayDomain,
    ApiGatewayIntegration,
    ApiGatewayMapping,
    ApiGatewayParsedUrl,
    ApiGatewayRoute,
)

from pathlib import Path
from furl import furl
from typing import List
from urllib.parse import urlparse

def url_parse(url: str) -> furl:
    parsed = furl(url)
    parsed.path.normalize()
    return parsed

class AwsApiGatewayDriver(MountDriver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology = ontology
        self.context = self.ontology.context
        self.account_id = self.context.account_id
        self.partition = self.context.partition
        self.region = self.context.region
        self.repo_name = self.context.repository_name
        self.statement_id = f"{self.partition}-{self.region}-{self.repo_name}"

    @classmethod
    def autocomplete(cls) -> List[str]:
        urls = []
        for domain in cls._domains():
            urls.append(domain.DomainName)
            for mapping in domain.Mappings:
                for route in mapping.Routes:
                    uri = route.RouteKey.split(" ")[-1]
                    full_path = str(furl(f"{domain.DomainName}/{mapping.ApiMappingKey}/{uri}"))
                    urls.append(full_path)

        if len(urls) == 0:
            return ["no discoverable api gateway endpoints (link to docs)"]
        return list(set(urls))

    @classmethod
    def _domains(cls) -> List[ApiGatewayDomain]:
        """
        This method returns domain objects with their related mappings, routes, and integrations
        domain =(has_many)=> mappings =(has_many)=> routes =(has_one)=> integration
        ex: domain.mappings[0].routes[0].integration
        """
        response = clients.api_gw.get_domain_names()
        domains = ApiGatewayDomains(**response).Items
        # filter domains to those with sentential tagging
        domains = [ domain for domain in domains if "sentential" in domain.Tags.keys() ]

        for domain in domains:
            response = clients.api_gw.get_api_mappings(DomainName=domain.DomainName)
            mappings = ApiGatewayMappings(**response).Items
            for mapping in mappings:
                domain.Mappings.append(mapping)
                response = clients.api_gw.get_routes(ApiId=mapping.ApiId)
                routes = ApiGatewayRoutes(**response).Items
                for route in routes:
                    mapping.Routes.append(route)
                    if route.Target:
                        integration_id = route.Target.split("/")[-1]
                        response = clients.api_gw.get_integration(
                            ApiId=mapping.ApiId, IntegrationId=integration_id
                        )
                        route.Integration = ApiGatewayIntegration(**response)
        return domains

    def mount(self, url: str, function: Function) -> ApiGatewayRoute:
        parsed_url = self._parse(url)
        integration = self._ensure_integration(parsed_url, function)
        route = self._ensure_route(parsed_url, integration)
        permission = self._ensure_permission(parsed_url, function)
        return route

    def umount(self, function: Function) -> None:
        to_delete = []
        for domain in self._domains():
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


    def _parse(self, path: str) -> ApiGatewayParsedUrl:
        # coerce schema if none
        if "https://" in path:
            pass
        elif "http://" in path:
            pass
        else:
            path = f"https://{path}"

        parsed = url_parse(path)

        for d in self._domains():
            # Try to find route already in existance.
            if d.DomainName == parsed.host:
                scheme = "https://"
                domain = f"{scheme}{d.DomainName}"
                for m in d.Mappings:
                    mapping = f"{m.ApiMappingKey}"
                    for r in m.Routes:
                        verb, route = r.RouteKey.split(" ")
                        found = url_parse(f"{domain}/{mapping}/{route}") 
                        if parsed.url == found.url:
                            return ApiGatewayParsedUrl(
                                ApiId=m.ApiId,
                                ApiMappingId=m.ApiMappingId,
                                ApiMappingKey=m.ApiMappingKey,
                                RouteId=r.RouteId,
                                RouteKey=r.RouteKey,
                                Route=route,
                                Verb=verb,
                                FullPath=str(found.path),
                            )

            # If no matching route integration already, return a new one.
                # sort so that "startswith" conditional matches against longest to shortest possibilities
                # example: if mappings ["/v1/api", "/v1"] exist, a given path of '/v1/api/subapp/' will register under '/v1/api' not '/v1'
                d.Mappings.sort(key=lambda m: len(m.ApiMappingKey), reverse=True)
                for m in d.Mappings:
                    mapping = m.ApiMappingKey
                    if str(parsed.path).startswith(mapping):
                        return ApiGatewayParsedUrl(
                            ApiId=m.ApiId,
                            ApiMappingId=m.ApiMappingId,
                            ApiMappingKey=m.ApiMappingKey,
                            RouteId=None,
                            RouteKey=f"ANY {parsed.path}",
                            Route=str(parsed.path),
                            FullPath=str(parsed.path),
                        )
        
        # else explode
        raise MountError(
            f"invalid url ({path}): bad formatting, could not find matching domain or mapping"
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
        response = clients.api_gw.get_integrations(ApiId=parsed_url.ApiId)
        integrations = ApiGatewayIntegrations(**response).Items
        for integration in integrations:
            if integration.IntegrationId is not None:
                integration.IntegrationId = None # set to none so comparison below can possibly be 1:1
                if desired_integration == integration:
                    return integration

        # else create the desired integration and return it
        desired_integration = desired_integration.dict(exclude={"IntegrationId"})
        desired_integration["ApiId"] = parsed_url.ApiId
        response = clients.api_gw.create_integration(**desired_integration)
        return ApiGatewayIntegration(**response)

    def _ensure_route(
        self, parsed_url: ApiGatewayParsedUrl, integration: ApiGatewayIntegration
    ) -> ApiGatewayRoute:
        target = f"integrations/{integration.IntegrationId}"
        
        verb, route = parsed_url.RouteKey.split(" ")
        if route.endswith("/"):
            route += '{proxy+}'
        elif not route.endswith("/"):
            route += '/{proxy+}'

        route_key_proxied = f"{verb} {route}"

        try:
            response = clients.api_gw.create_route(
                ApiId=parsed_url.ApiId,
                RouteKey=route_key_proxied,
                Target=target,
            )
        except clients.api_gw.exceptions.ConflictException:
            response = clients.api_gw.update_route(
                ApiId=parsed_url.ApiId,
                RouteId=parsed_url.RouteId,
                RouteKey=route_key_proxied,
                Target=target,
            )
        return ApiGatewayRoute(**response)

    def _ensure_permission(self, parsed_url: ApiGatewayParsedUrl, function: Function):
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
