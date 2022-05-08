from pydantic import BaseModel, ValidationError, validator
from typing import Dict, List, Optional
from humps import camelize


def to_camel(string):
    return camelize(string)


class CamelModel(BaseModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


class HttpStruct(CamelModel):
    method: str
    path: str
    protocol: str = "HTTP/1.1"
    source_ip: Optional[str]
    user_agent: Optional[str]

    @validator("method")
    def validate_method(cls, v):
        valid_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]  # noqa: E501
        if v in valid_methods:
            return v
        else:
            raise ValidationError(f"{v} not a valid HTTP verb")


class RequestContextStruct(CamelModel):
    account_id: Optional[str]
    authentication: Optional[str]
    authorizer: Optional[Dict]
    domain_name: Optional[str]
    domain_prefix: str = "id"
    http: HttpStruct
    request_id: Optional[str]
    route_key: str = "$default"
    stage: str = "$default"
    time: Optional[str]
    time_epoch: Optional[int]


class APIGatewayV2Event(CamelModel):
    version: str = "2.0"
    route_key: str = "$default"
    raw_path: str
    raw_query_string: Optional[str]
    cookies: List[str]
    headers: Dict[str, str]
    query_string_parameters: Optional[Dict[str, str]]
    request_context: RequestContextStruct
    body: Optional[str]
    path_parameters: Optional[Dict[str, str]]
    is_base_64_encoded: bool = False
    stage_variables: Optional[Dict[str, str]]


class APIGatewayV2Response(CamelModel):
    status_code: int
    body: str
    headers: Dict
    is_base_64_encoded: bool
