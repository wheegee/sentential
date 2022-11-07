from sentential.lib.drivers.spec import MountDriver
from sentential.lib.exceptions import MountError
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import (
    Function,
    ApiGatewayDomains,
    ApiGatewayIntegrations,
    ApiGatewayMappings,
    ApiGatewayRoutes,
    ApiGatewayDomain,
    ApiGatewayIntegration,
    ApiGatewayParsedUrl,
    ApiGatewayRoute,
)

from pathlib import Path
from typing import List

def pathify(segements: List[str]) -> str:
    """take in url segments, drop blanks, join them again, and deduplicate slashes"""
    joined = "/".join(segment for segment in segements if segment)
    return str(Path(joined))

def deproxy(url: str) -> str:
    """remove api gateway proxy strings from url"""
    url = url.replace("{proxy+}","").replace("{proxy}","")
    return str(Path(url))

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
            found_domain = domain.DomainName
            urls.append(found_domain)
            for mapping in domain.Mappings:
                found_mapping = mapping.ApiMappingKey
                for route in mapping.Routes:
                    found_verb, found_route = route.RouteKey.split(" ")
                    url = deproxy(pathify([found_domain, found_mapping, found_route]))
                    urls.append(url)

        if len(urls) == 0:
            return ["no discoverable api gateway endpoints (link to docs)"]
        return list(set(urls))

    @classmethod
    def _domains(cls) -> List[ApiGatewayDomain]:
        """
        This method returns domain objects with their related mappings, routes, and integrations
        domain =(has_many)=> mappings =(has_many)=> routes =(has_one)=> integration
        ex: domain.mappings[*].routes[*].integration
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

    @classmethod
    def _parse(cls, url: str) -> ApiGatewayParsedUrl:
        given_url = str(Path(url))
        given_host, *given_route = given_url.split("/")
        given_route = deproxy(pathify(given_route))
        domains = cls._domains()
        # Try to find route already in existance.
        for domain in domains:
            found_host = domain.DomainName
            if found_host == given_host:
                for mapping in domain.Mappings:
                    found_mapping = mapping.ApiMappingKey
                    for route in mapping.Routes:
                        found_verb, found_route = route.RouteKey.split(" ")
                        found_url = deproxy(pathify([found_host, found_mapping, found_route]))
                        if found_url == given_url:
                            return ApiGatewayParsedUrl(
                                ApiId=mapping.ApiId,
                                ApiMappingId=mapping.ApiMappingId,
                                ApiMappingKey=mapping.ApiMappingKey,
                                RouteId=route.RouteId,
                                RouteKey=route.RouteKey,
                                Route=f"/{given_route}",
                                Verb=found_verb,
                                FullPath=given_url,
                            )

        # If no matching route integration already, return a new one under valid mapping.
        for domain in domains:
            found_host = domain.DomainName
            domain.Mappings.sort(key=lambda m: len(m.ApiMappingKey), reverse=True)
            if found_host == given_host:
                for mapping in domain.Mappings:
                    if given_route.startswith(mapping.ApiMappingKey):
                        return ApiGatewayParsedUrl(
                            ApiId=mapping.ApiId,
                            ApiMappingId=mapping.ApiMappingId,
                            ApiMappingKey=mapping.ApiMappingKey,
                            RouteId=None,
                            RouteKey=f"ANY /{given_route}/{{proxy+}}",
                            Route=f"/{given_route}",
                            Verb="ANY",
                            FullPath=given_url,
                        )
        
        # else explode
        raise MountError(
            f"could not find valid domain and/or mapping for {given_url}"
        )

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

        try:
            clients.lmb.remove_permission(
                FunctionName=function.name,
                StatementId=self.statement_id,
            )
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass


    def ls(self, function: Function) -> List[ApiGatewayParsedUrl]:
        results = []
        for domain in self._domains():
            found_domain = domain.DomainName
            for mapping in domain.Mappings:
                found_mapping = mapping.ApiMappingKey
                for route in mapping.Routes:
                    if route.Integration:
                        if route.Integration.IntegrationUri == function.arn:
                            found_verb, found_route = route.RouteKey.split(" ")
                            url = deproxy(pathify([found_domain, found_mapping, found_route]))
                            results.append(url)
        return results

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
                integration_id = integration.IntegrationId
                integration.IntegrationId = None # set to none so comparison below can possibly be 1:1
                if desired_integration == integration:
                    integration.IntegrationId = integration_id
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
        
        route = parsed_url.Route
        verb = parsed_url.Verb

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
