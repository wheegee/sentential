from sentential.lib.drivers.spec import MountDriver
from sentential.lib.exceptions import MountError
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import (
    ApiGatewayIntegrations,
    ApiGatewayRoute,
    ExistingRoute,
    Function,
    ApiGatewayDomains,
    ApiGatewayMappings,
    ApiGatewayRoutes,
    ApiGatewayDomain,
    ApiGatewayIntegration,
    LambdaPermissionResponse,
    NewRoute,
)

from pathlib import Path
from typing import List, Union

def pathify(segments: List[str]) -> str:
    """take in url segments, drop blanks, join them again, and deduplicate slashes, prepend with slash"""
    joined = "/".join(segment for segment in segments if segment)
    pathed = str(Path(joined))
    if pathed == ".":
        return "/"
    return f"/{pathed}" 

def fqdnify(segments: List[str]) -> str:
    """take in url segments, drop blanks, join them again, and deduplicate slashes"""
    joined = "/".join(segment for segment in segments if segment)
    fqdned = str(Path(joined))
    return fqdned

def deproxy(url: str) -> str:
    """remove api gateway proxy strings from url"""
    url = url.replace("{proxy+}", "").replace("{proxy}", "")
    return str(Path(url))

class AwsApiGatewayDriver(MountDriver):
    def __init__(self, ontology: Ontology, function: Function) -> None:
        self.function = function
        self.ontology = ontology
        self.context = self.ontology.context
        self.account_id = self.context.account_id
        self.partition = self.context.partition
        self.region = self.context.region
        self.repo_name = self.context.repository_name
        self.statement_id = f"{self.partition}-{self.region}-{self.repo_name}"

    @classmethod
    def _domains(cls) -> List[ApiGatewayDomain]:
        response = clients.api_gw.get_domain_names()
        domains = ApiGatewayDomains(**response).Items
        # filter domains to those with sentential tagging
        domains = [domain for domain in domains if "sentential" in domain.Tags.keys()]
        return domains

    @classmethod
    def _all_mounts(cls) -> List[ApiGatewayDomain]:
        """
        This method returns domain objects with their related mappings, routes, and integrations
        domain =(has_many)=> mappings =(has_many)=> routes =(has_one)=> integration
        ex: domain.mappings[*].routes[*].integration
        """
        all_mounts = cls._domains()
        for domain in all_mounts:
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
        return all_mounts

    @classmethod
    def _to_urls(cls, domains: List[ApiGatewayDomain], include_roots: bool = False) -> List[str]:
        # NOTE: include_roots is for convenience when autocompleting, not to be used anywhere else
        urls = []
        for domain in domains:
            found_domain = domain.DomainName
            if include_roots:
                urls.append(found_domain)
            for mapping in domain.Mappings:
                for route in mapping.Routes:
                    found_verb, found_route = route.RouteKey.split(" ")
                    url = deproxy(fqdnify([found_domain, found_route]))
                    urls.append(url)

        return list(set(urls))

    @classmethod
    def autocomplete(cls) -> List[str]:
        return cls._to_urls(cls._all_mounts(), True)

    def _mounts(self) -> List[ApiGatewayDomain]:
        domains = self._all_mounts()
        for domain in domains:
            for mapping in domain.Mappings:
                for route in mapping.Routes:
                    if route.Integration:
                        if route.Integration.IntegrationUri != self.function.arn:
                            mapping.Routes.remove(route)
                
                if len(mapping.Routes) == 0:
                    domain.Mappings.remove(mapping)
            if len(domain.Mappings) == 0:
                domains.remove(domain)

        return domains

    def mounts(self) -> List[str]:
        mounts = self._to_urls(self._mounts())
        return mounts

    def mount(self, url: str) -> ApiGatewayRoute:
        parsed_url: Union[NewRoute, ExistingRoute] = self._parse(url)
        integration: ApiGatewayIntegration = self._ensure_integration(parsed_url)
        route = self._ensure_route(parsed_url, integration)
        permission = self._ensure_permission(parsed_url)
        return route

    def umount(self, url: str) -> None:
        unmounted = []
        if url == "ALL":
            for domain in self._mounts():
                for mapping in domain.Mappings:
                    for route in mapping.Routes:
                        if route.Integration:
                            # TODO: figure out how to get this more strictly typed without breaking the other things.
                            self._umount(mapping.ApiId, route.RouteId, route.Integration.IntegrationId)

        elif url:
            parsed_url = self._parse(url)
            if isinstance(parsed_url, ExistingRoute):
                # TODO: figure out how to get this more strictly typed without breaking the other things.
                self._umount(parsed_url.ApiId, parsed_url.RouteId, parsed_url.Integration.IntegrationId )
            elif isinstance(parsed_url, NewRoute):
                raise MountError(f"no such mount {url}")


    def _parse(self, url: str) -> Union[ExistingRoute, NewRoute]:
        given_host, *given_path = url.split("/")
        given_path = pathify(given_path)
        parsed_url = None
        domains = self._all_mounts()
        for domain in domains:
            if domain.DomainName == given_host:
                for mapping in domain.Mappings:
                    for route in mapping.Routes:
                        found_verb, found_path = route.RouteKey.split(" ")
                        if deproxy(found_path) == given_path:
                            if route.Integration:
                                if route.Integration.IntegrationUri == self.function.arn:
                                    existing = dict(route)
                                    existing['ApiId'] = mapping.ApiId
                                    return ExistingRoute(**existing)
                                else:
                                    raise MountError(f"{route.Integration.IntegrationId} already mounted to {url}")
        
        for domain in domains:
            if domain.DomainName == given_host:
                if given_path == "/":
                    proxy_path = "/{proxy+}"
                else:
                    proxy_path = f"{given_path}/{{proxy+}}"

                return NewRoute(
                    ApiId=domain.Mappings[0].ApiId,
                    RouteKey=f"ANY {proxy_path}",
                )
        
        raise MountError(f"no viable domain to mount against for {given_host}")



    def _ensure_integration(
        self, parsed_url: Union[NewRoute, ExistingRoute]
    ) -> ApiGatewayIntegration:

        forwarded_prefix = deproxy(parsed_url.RouteKey.split(" ")[-1])

        desired_integration = ApiGatewayIntegration(
            IntegrationId=None,
            IntegrationUri=self.function.arn,
            RequestParameters={
                "overwrite:path": "/$request.path.proxy",
                "overwrite:header.X-Forwarded-Prefix": forwarded_prefix,
            },
        )

        # if the desired integration already exists, return it
        response = clients.api_gw.get_integrations(ApiId=parsed_url.ApiId)
        integrations = ApiGatewayIntegrations(**response).Items
        for integration in integrations:
            if integration.IntegrationId is not None:
                integration_id = integration.IntegrationId
                integration.IntegrationId = (
                    None  # set to none so comparison below can possibly be 1:1
                )
                if desired_integration == integration:
                    integration.IntegrationId = integration_id
                    return integration

        # else create the desired integration and return it
        desired_integration = desired_integration.dict(exclude={"IntegrationId"})
        desired_integration["ApiId"] = parsed_url.ApiId
        response = clients.api_gw.create_integration(**desired_integration)
        return ApiGatewayIntegration(**response)

    def _ensure_route(
        self, parsed_url: Union[ExistingRoute, NewRoute], integration: ApiGatewayIntegration
    ) -> ApiGatewayRoute:

        target = f"integrations/{integration.IntegrationId}"

        if isinstance(parsed_url, NewRoute):
            response = clients.api_gw.create_route(
                ApiId=parsed_url.ApiId,
                RouteKey=parsed_url.RouteKey,
                Target=target,
            )

        elif isinstance(parsed_url, ExistingRoute):
            response = clients.api_gw.update_route(
                ApiId=parsed_url.ApiId,
                RouteId=parsed_url.RouteId,
                RouteKey=parsed_url.RouteKey,
                Target=target,
            )
        
        else:
            raise MountError("route is neither new nor existing type")

        return ApiGatewayRoute(**response)

    def _ensure_permission(self, parsed_url: Union[NewRoute, ExistingRoute]) -> LambdaPermissionResponse:
        try:
            clients.lmb.remove_permission(
                FunctionName=self.function.name,
                StatementId=self.statement_id,
            )
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass

        response = clients.lmb.add_permission(
            FunctionName=self.function.arn,
            StatementId=self.statement_id,
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{self.region}:{self.account_id}:{parsed_url.ApiId}/*/*/{{proxy+}}",
        )
        return LambdaPermissionResponse(**response)

    def _umount(self, api_id: str, route_id: str, integration_id: str):
        self._delete_route(api_id, route_id)
        self._delete_integration(api_id, integration_id)
        self._delete_permission()

    def _delete_route(self, api_id: str, route_id: str) -> None:
        try:
            clients.api_gw.delete_route(ApiId=api_id, RouteId=route_id)
        except clients.api_gw.exceptions.NotFoundException:
            pass

    def _delete_integration(self, api_id: str, integration_id: str) -> None:
        try:
            clients.api_gw.delete_integration(
                ApiId=api_id,
                IntegrationId=integration_id,
            )
        except clients.api_gw.exceptions.NotFoundException:
            pass

    def _delete_permission(self) -> None:
        try:
            clients.lmb.remove_permission(
                FunctionName=self.function.name,
                StatementId=self.statement_id,
            )
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass