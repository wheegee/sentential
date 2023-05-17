import os
from datetime import datetime
from enum import Enum
from pathlib import PosixPath
from typing import Any, List, Union, Optional, Dict, Literal
from pydantic import Field, validator, Json, Extra
from pydantic import BaseModel as BaseModel
from sentential.lib.exceptions import ShapeError
from sentential.lib.clients import clients


#
# Global Constants
#

SNTL_WORKING_IMAGE_TAG = os.getenv("SNTL_WORKING_IMAGE_TAG", default=("cwi"))
SNTL_ENTRY_VERSION = os.getenv("SNTL_ENTRY_VERSION", default=("0.4.2"))

#
# Store
#


class UndefinedStoreModel(BaseModel):
    ...

    class Config:
        validate_all = True
        extra = Extra.allow


class StoreModel(BaseModel):
    ...

    class Config:
        validate_all = True
        extra = Extra.forbid


class Args(UndefinedStoreModel):
    ...


class Envs(UndefinedStoreModel):
    ...


class Secrets(UndefinedStoreModel):
    ...


class Tags(UndefinedStoreModel):
    ...


class Configs(StoreModel):
    storage: int = Field(default=512, description="ephemeral storage (mb)")
    memory: int = Field(default=128, description="allocated memory (mb)")
    timeout: int = Field(default=3, description="timeout (s)")
    subnet_ids: List[str] = Field(default=[], description="subnet ids")
    security_group_ids: List[str] = Field(default=[], description="security group ids")
    auth_type: Literal["NONE", "AWS_IAM"] = Field(
        default="NONE", description="auth type"
    )
    allow_headers: List[str] = Field(default=["*"], description="CORS AllowHeaders")
    allow_methods: List[str] = Field(default=["*"], description="CORS AllowMethods")
    allow_origins: List[str] = Field(default=["*"], description="CORS AllowOrigins")
    expose_headers: List[str] = Field(default=["*"], description="CORS ExposeHeaders")
    log_retention: int = Field(default=7, description="log retention (days)")


#
# Architecture
#

# https://github.com/BretFisher/multi-platform-docker-build
#   Value    Normalized
#   aarch64  arm64      # the latest v8 arm architecture. Used on Apple M1, AWS Graviton, and Raspberry Pi 3's and 4's
#   armhf    arm        # 32-bit v7 architecture. Used in Raspberry Pi 3 and  Pi 4 when 32bit Raspbian Linux is used
#   armel    arm/v6     # 32-bit v6 architecture. Used in Raspberry Pi 1, 2, and Zero
#   i386     386        # older Intel 32-Bit architecture, originally used in the 386 processor
#   x86_64   amd64      # all modern Intel-compatible x84 64-Bit architectures
#   x86-64   amd64      # same


class Architecture(Enum):
    amd64 = "amd64"
    arm64 = "arm64"

    @classmethod
    def system(cls):
        sys_arch = clients.docker.system.info().architecture
        try:
            normalized = {"aarch64": "arm64", "x86_64": "amd64", "x86-64": "amd64"}[
                sys_arch
            ]
            return getattr(cls, normalized)
        except KeyError:
            print(
                f"there was an issue normalizing your host arch {sys_arch} to arm64 or amd64"
            )
            print("defaulting to amd64")
            return cls.amd64


#
# SSM
#


class AwsSSMParam(BaseModel):
    Name: str
    Type: Literal["String", "StringList", "SecureString"]
    Value: str
    Version: int
    Selector: Optional[str]
    SourceResult: Optional[str]
    LastModifiedDate: datetime
    ARN: str
    DataType: str


#
# ECR
#


# describe_image()
class AwsImageDescription(BaseModel):
    imageDigest: str
    imageTags: Union[List[str], None]
    imageManifestMediaType: str


class AwsImageDescriptions(BaseModel):
    imageDetails: List[AwsImageDescription]


# Manifest List
# https://docs.docker.com/registry/spec/manifest-v2-2/


class AwsManifestListManifestPlatform(BaseModel):
    architecture: str
    os: str


class AwsManifestListDistribution(BaseModel):
    mediaType: str = "application/vnd.docker.distribution.manifest.v2+json"
    size: int
    digest: str
    platform: AwsManifestListManifestPlatform


class AwsManifestList(BaseModel):
    schemaVersion: int = 2
    mediaType: str = "application/vnd.docker.distribution.manifest.list.v2+json"
    manifests: List[AwsManifestListDistribution]


# Image Manifest
# https://docs.docker.com/registry/spec/manifest-v2-2/


class AwsImageManifestLayer(BaseModel):
    mediaType: str = "application/vnd.docker.image.rootfs.diff.tar.gzip"
    size: int
    digest: str


class AwsImageManifest(BaseModel):
    schemaVersion: int = 2
    mediaType: str = "application/vnd.docker.distribution.manifest.v2+json"
    config: AwsImageManifestLayer
    layers: List[AwsImageManifestLayer]


# batch_get_image()
class AwsImageDetailImageId(BaseModel):
    imageDigest: str
    imageTag: Optional[str]


class AwsImageDetail(BaseModel):
    registryId: str
    repositoryName: str
    imageId: AwsImageDetailImageId
    imageManifest: Union[Json[AwsImageManifest], Json[AwsManifestList]]


class AwsImageDetails(BaseModel):
    images: List[AwsImageDetail]


class AwsEcrAuthorizationData(BaseModel):
    authorizationToken: str
    expiresAt: datetime
    proxyEndpoint: str


class AwsEcrAuthorizationToken(BaseModel):
    authorizationData: List[AwsEcrAuthorizationData]


#
# IAM
#


class AWSPolicyStatement(BaseModel):
    """https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_statement.html"""

    Effect: str
    Action: Union[str, List[str]]
    Principal: Optional[dict]
    Resource: Optional[Union[str, List[str]]]
    Condition: Optional[dict]


class AWSPolicyDocument(BaseModel):
    """https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html"""

    Version: str = "2012-10-17"
    Statement: List[AWSPolicyStatement]


class AWSCallerIdentity(BaseModel):
    UserId: str
    Account: str
    Arn: str
    type: Optional[bool]

    @validator("type", always=True)
    def derive_type(cls, value, values):
        if ":federated-user/" in values["Arn"]:
            return "federated-user"
        elif ":assumed-role/" in values["Arn"]:
            return "assumed-role"
        elif ":user/" in values["Arn"]:
            return "user"
        else:
            raise ShapeError(
                f"could not determine credential type of...\n{values['Arn']}"
            )


class AWSCredentials(BaseModel):
    AccessKeyId: str
    SecretAccessKey: str
    SessionToken: Optional[str]
    Expiration: Optional[datetime]


class AWSFederatedUser(BaseModel):
    FederatedUserId: str
    Arn: str


class AWSAssumedRoleUser(BaseModel):
    AssumedRoleId: str
    Arn: str


class AWSFederationToken(BaseModel):
    Credentials: AWSCredentials
    FederatedUser: AWSFederatedUser
    PackedPolicySize: int


class AWSAssumeRole(BaseModel):
    Credentials: AWSCredentials
    AssumedRoleUser: AWSAssumedRoleUser


#
# Lambda
#


class Runtimes(Enum):
    """https://gallery.ecr.aws/lambda?page=1"""

    python = "python"
    dotnet = "dotnet"
    java = "java"
    go = "go"
    nodejs = "nodejs"
    provided = "provided"
    ruby = "ruby"


LAMBDA_ROLE_POLICY_JSON = (
    AWSPolicyDocument(
        Statement=[
            AWSPolicyStatement(
                Effect="Allow",
                Principal={"Service": "lambda.amazonaws.com"},
                Action="sts:AssumeRole",
            )  # type: ignore
        ]
    )
).json(exclude_none=True)


class AwsFunctionVpcConfig(BaseModel):
    SubnetIds: List[str]
    SecurityGroupIds: List[str]
    VpcId: str


class AwsFunctionEnvironment(BaseModel):
    Variables: Dict[str, str]


class AwsFunctionEphemeralStorage(BaseModel):
    Size: int


class AwsFunctionConfiguration(BaseModel):
    FunctionName: str
    FunctionArn: str
    Role: str
    CodeSize: int
    Description: str
    Timeout: int
    MemorySize: int
    LastModified: datetime
    CodeSha256: str
    Version: str
    VpcConfig: AwsFunctionVpcConfig
    Environment: AwsFunctionEnvironment
    TracingConfig: Dict[str, str]
    RevisionId: str
    State: str
    StateReason: Optional[str]
    StateReasonCode: Optional[str]
    PackageType: str
    Architectures: List[str]
    EphemeralStorage: AwsFunctionEphemeralStorage


class AwsFunctionCode(BaseModel):
    RepositoryType: str
    ImageUri: str
    ResolvedImageUri: str


class AwsFunctionCors(BaseModel):
    AllowHeaders: List[str]
    AllowMethods: List[str]
    AllowOrigins: List[str]
    ExposeHeaders: List[str]


class AwsFunctionPublicUrl(BaseModel):
    FunctionUrl: str
    FunctionArn: str
    AuthType: str
    Cors: AwsFunctionCors
    CreationTime: datetime
    LastModifiedTime: datetime


class AwsFunction(BaseModel):
    Configuration: AwsFunctionConfiguration
    Code: AwsFunctionCode


#
# Pathing
#


class Paths(BaseModel):
    root: PosixPath
    src: PosixPath
    dockerfile: PosixPath
    policy: PosixPath
    shapes: PosixPath


def derive_paths(root: PosixPath = PosixPath(".")):
    return Paths(
        root=root,
        src=PosixPath(f"{root}/src"),
        dockerfile=PosixPath(f"{root}/Dockerfile"),
        policy=PosixPath(f"{root}/policy.json"),
        shapes=PosixPath(f"{root}/shapes.py"),
    )


#
# API Gateway
#


class ApiGatewayApi(BaseModel):
    ApiId: str
    ApiEndpoint: str
    ApiKeySelectionExpression: str
    CreatedDate: datetime
    DisableExecuteApiEndpoint: bool
    Name: str
    ProtocolType: str
    RouteSelectionExpression: str
    Tags: Dict[str, str]


class ApiGatewayIntegration(BaseModel):
    IntegrationId: Optional[str]
    IntegrationUri: str
    ConnectionType: str = "INTERNET"
    Description: str = "managed by sentential"
    IntegrationMethod: str = "ANY"
    IntegrationType: str = "AWS_PROXY"
    PayloadFormatVersion: str = "2.0"
    TimeoutInMillis: int = 30000
    RequestParameters: Optional[Dict[str, str]] = {}


class ApiGatewayRoute(BaseModel):
    ApiGatewayManaged: Optional[bool]
    ApiKeyRequired: bool
    AuthorizationScopes: Optional[List[str]]
    AuthorizationType: Literal["NONE", "AWS_IAM", "CUSTOM", "JWT"]
    AuthorizerId: Optional[str]
    ModelSelectionExpression: Optional[str]
    OperationName: Optional[str]
    RequestModels: Optional[Dict[str, str]]
    RequestParameters: Optional[Dict[str, Dict[Literal["Required"], bool]]]
    RouteId: str
    RouteKey: str
    RouteResponseSelectionExpression: Optional[str]
    Target: Optional[str]


class LambdaPermission(BaseModel):
    Statement: Json[AWSPolicyStatement]


class LambdaInvokeResponse(BaseModel):
    ResponseMetadata: Dict
    StatusCode: int
    Payload: str


#
# EventBridge
#


class EbrDescribeRuleResponse(BaseModel):
    Name: str
    Arn: str
    ScheduleExpression: str
    State: str
    EventBusName: str
    CreatedBy: str
    ResponseMetadata: Dict[str, Any]
    RetryAttempts: Optional[int]


class EbrPutRuleResponse(BaseModel):
    RuleArn: str
    ResponseMetadata: Dict[str, Any]
    RetryAttempts: Optional[int]
