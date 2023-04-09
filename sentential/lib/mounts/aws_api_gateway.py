from functools import lru_cache
from typing import cast, Dict, List, Union, Tuple
from sentential.lib.mounts.spec import MountDriver
from sentential.lib.clients import clients
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import (
    Configs,
    ApiGatewayApi,
    ApiGatewayRoute,
    ApiGatewayIntegration,
    LambdaPermission,
)
from sentential.lib.exceptions import AwsApiGatewayNotFound


def proxify(path: str) -> str:
    # In theory all other edge cases are handled by the AWS api
    greedy_proxy = "{proxy+}"
    if path.endswith(f"/{greedy_proxy}"):
        return path
    elif path.endswith("/"):
        return f"{path[:-1]}/{greedy_proxy}"
    else:
        return f"{path}/{greedy_proxy}"


def deproxify(path: str) -> str:
    # In theory all other edge cases are handled by the AWS api
    proxy_strings = ["{proxy+}", "{proxy}"]
    for proxy_string in proxy_strings:
        if path.endswith(proxy_string):
            path = path.replace(proxy_string, "")

    if not path.endswith("/"):
        path = f"{path}/"

    return path


class AwsApiGatewayMount(MountDriver):
    def __init__(self, ontology: Ontology) -> None:
        self.ontology: Ontology = ontology
        self.resource_name: str = self.ontology.context.resource_name
        self.resource_arn: str = self.ontology.context.resource_arn
        self.provision = cast(Configs, self.ontology.configs.parameters)

        # set by _fetch_state
        self.path: str
        self.given_host: str
        self.given_route: str
        self.route_key: str
        self.api: ApiGatewayApi
        self.route: Union[None, ApiGatewayRoute]
        self.integration: Union[None, ApiGatewayIntegration]
        self.statement_id: str

    @classmethod
    def autocomplete(cls) -> List[str]:
        completions = []
        for api in cls._apis():
            host = api.ApiEndpoint.replace(
                "https://", ""
            )  # https://github.com/pallets/click/issues/1515
            completions.append(host)
            for route in cls._routes(api.ApiId):
                path = deproxify(route.RouteKey.split(" ")[-1])
                completions.append(f"{host}{path}")
        return completions

    @classmethod
    def _apis(cls) -> List[ApiGatewayApi]:
        return [ApiGatewayApi(**item) for item in clients.api_gw.get_apis()["Items"]]

    @classmethod
    def _routes(cls, api_id: str) -> List[ApiGatewayRoute]:
        return [
            ApiGatewayRoute(**item)
            for item in clients.api_gw.get_routes(ApiId=api_id)["Items"]
        ]

    @classmethod
    def _integrations(cls, api_id: str) -> List[ApiGatewayIntegration]:
        return [
            ApiGatewayIntegration(**item)
            for item in clients.api_gw.get_integrations(ApiId=api_id)["Items"]
        ]

    def mount(self, path: str) -> str:
        self._fetch_state(path)
        integration = self._ensure_integration()
        route = self._ensure_route(integration)
        policy = self._ensure_policy()
        resource = self.ontology.context.resource_name
        location = deproxify(f"{self.api.ApiEndpoint}{self.given_route}")
        return f"mounted {resource} to {location}"

    def umount(self, path: Union[None, str] = None) -> List[str]:
        mounts = self._mounts()
        umounted = []
        resource = self.ontology.context.resource_name

        if path:
            if not path.startswith("https://"):
                path = f"https://{path}"
            path = deproxify(path)

        for api, route, integration in mounts:
            location = deproxify(f"{api.ApiEndpoint}{route.RouteKey.split(' ')[-1]}")

            if path and path != location:
                continue

            clients.api_gw.delete_route(ApiId=api.ApiId, RouteId=route.RouteId)

            clients.api_gw.delete_integration(
                ApiId=api.ApiId, IntegrationId=integration.IntegrationId
            )

            try:
                clients.lmb.remove_permission(
                    FunctionName=self.ontology.context.resource_name,
                    StatementId=f"{self.ontology.context.resource_name}-{api.ApiId}",
                )
            except clients.lmb.exceptions.ResourceNotFoundException:
                pass

            umounted.append(f"umounted {resource} from {location}")
        return umounted

    def mounts(self) -> List[str]:
        mounts = []
        for api, route, integration in self._mounts():
            host = api.ApiEndpoint.replace(
                "https://", ""
            )  # https://github.com/pallets/click/issues/1515
            path = deproxify(route.RouteKey.split(" ")[-1])
            mounts.append(f"{host}{path}")
        return mounts

    def _mounts(
        self,
    ) -> List[Tuple[ApiGatewayApi, ApiGatewayRoute, ApiGatewayIntegration]]:
        mounts = []
        for api in self.__class__._apis():
            routes = self.__class__._routes(api.ApiId)
            integrations = self.__class__._integrations(api.ApiId)
            for route in routes:
                if route.Target:
                    for integration in integrations:
                        if integration.IntegrationId:
                            if integration.IntegrationId in route.Target:
                                mounts.append((api, route, integration))
        return mounts

    @lru_cache
    def _fetch_state(self, path: str) -> None:
        given_host, *given_route = path.split("/")
        self.path = path
        self.given_host = given_host
        self.given_route = f"/{'/'.join(given_route)}"
        self.route_key = f"ANY {self.given_route}"
        self.api = self._get_api()
        self.api_id = self.api.ApiId
        self.route = self._get_route()
        self.integration = self._get_integration()
        self.statement_id = f"{self.ontology.context.resource_name}-{self.api.ApiId}"

    def _get_api(self) -> ApiGatewayApi:
        for api in self.__class__._apis():
            found_host = api.ApiEndpoint.replace(
                "https://", ""
            )  # https://github.com/pallets/click/issues/1515
            if found_host == self.given_host:
                return api
        raise AwsApiGatewayNotFound

    def _get_route(self) -> Union[None, ApiGatewayRoute]:
        for route in self.__class__._routes(self.api.ApiId):
            if route.RouteKey == self.route_key:
                return route
        return None

    def _get_integration(self) -> Union[None, ApiGatewayIntegration]:
        if self.route and self.route.Target:
            return ApiGatewayIntegration(
                **clients.api_gw.get_integration(
                    ApiId=self.api.ApiId, IntegrationId=self.route.Target.split("/")[-1]
                )
            )
        else:
            return None

    def _ensure_integration(self) -> ApiGatewayIntegration:
        integration = {
            "ApiId": self.api.ApiId,
            "IntegrationUri": self.ontology.context.resource_arn,
            "IntegrationMethod": "ANY",
            "IntegrationType": "AWS_PROXY",
            "PayloadFormatVersion": "2.0",
            "TimeoutInMillis": (self.provision.timeout * 1000),
            "RequestParameters": {
                "overwrite:path": "/$request.path.proxy",
                "overwrite:header.X-Forwarded-Prefix": deproxify(self.given_route),
            },
        }

        if self.integration:
            integration["IntegrationId"] = self.integration.IntegrationId
            return ApiGatewayIntegration(
                **clients.api_gw.update_integration(**integration)
            )
        else:
            return ApiGatewayIntegration(
                **clients.api_gw.create_integration(**integration)
            )

    def _ensure_route(self, integration: ApiGatewayIntegration) -> ApiGatewayRoute:
        route = {
            "ApiId": self.api.ApiId,
            "RouteKey": f"ANY {proxify(self.given_route)}",
            "Target": f"integrations/{integration.IntegrationId}",
        }

        if self.route:
            route["RouteId"] = self.route.RouteId
            return ApiGatewayRoute(**clients.api_gw.update_route(**route))
        else:
            return ApiGatewayRoute(**clients.api_gw.create_route(**route))

    def _ensure_policy(self) -> LambdaPermission:
        account_id = self.ontology.context.account_id
        region = self.ontology.context.region

        try:
            clients.lmb.remove_permission(
                FunctionName=self.ontology.context.resource_name,
                StatementId=self.statement_id,
            )
        except clients.lmb.exceptions.ResourceNotFoundException:
            pass

        return LambdaPermission(
            **clients.lmb.add_permission(
                FunctionName=self.ontology.context.resource_arn,
                StatementId=self.statement_id,
                Action="lambda:InvokeFunction",
                Principal="apigateway.amazonaws.com",
                SourceArn=f"arn:aws:execute-api:{region}:{account_id}:{self.api.ApiId}/*/*/{{proxy+}}",
            )
        )
