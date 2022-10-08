from enum import Enum
from lib2to3.pgen2.token import OP
from pathlib import PosixPath
from typing import List, Union, Optional
from pydantic import BaseModel, Field, validator
from sentential.support.shaper import Shaper
import polars as pl

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


#
# Pathing
#
class Paths(BaseModel):
    root: PosixPath
    sntl: PosixPath
    src: PosixPath
    dockerfile: PosixPath
    wrapper: PosixPath
    policy: PosixPath
    shapes: PosixPath


def derive_paths(root: PosixPath = PosixPath(".")):
    return Paths(
        root=root,
        sntl=PosixPath(f"{root}/.sntl"),
        src=PosixPath(f"{root}/src"),
        dockerfile=PosixPath(f"{root}/Dockerfile"),
        wrapper=PosixPath(f"{root}/.sntl/wrapper.sh"),
        policy=PosixPath(f"{root}/policy.json"),
        shapes=PosixPath(f"{root}/shapes.py"),
    )


#
# Internally Defined Shapes
#

# TODO:
# - tags: validation should sort by semver
# - digests: validation should run a deduplication
# - arch: wtf is going on with the ecr API around this?


class Image(BaseModel):
    id: str
    digest: Union[str, None]
    tags: List[str]
    versions: List[str]
    # arch: str

    @validator("versions")
    def coerce_versions(cls, v):
        if v is not None:
            uniq = list(set(v))
            return uniq
        else:
            return []

    @validator("tags")
    def coerce_tags(cls, v):
        if v is not None:
            uniq = list(set(v))
            return uniq
        else:
            return []


class ImageView(Image):
    href: List[str] = []

    @validator("href")
    def uniq(cls, v):
        return list(set(v))

    @validator("id")
    def humanize_id(cls, v):
        return v.replace("sha256:", "")[0:12]

    @validator("digest")
    def humanize_digest(cls, v):
        if v:
            return v.replace("sha256:", "")[0:12]


class Function(BaseModel):
    image: Image
    region: str
    arn: str
    function_name: str
    web_console_url: Union[str, None]
    public_url: Union[str, None]


class Provision(Shaper):
    storage: int = Field(default=512, description="ephemeral storage (mb)")
    memory: int = Field(default=128, description="allocated memory (mb)")
    timeout: int = Field(default=3, description="timeout (s)")
    subnet_ids: List[str] = Field(default=[], description="subnet ids")
    security_group_ids: List[str] = Field(default=[], description="security group ids")
    auth_type: str = Field(default="NONE", description="auth type (--public-url)")
    allow_headers: List[str] = Field(
        default=["*"], description="CORS AllowHeaders (--public-url)"
    )
    allow_methods: List[str] = Field(
        default=["*"], description="CORS AllowMethods (--public-url)"
    )
    allow_origins: List[str] = Field(
        default=["*"], description="CORS AllowOrigins (--public-url)"
    )
    expose_headers: List[str] = Field(
        default=["*"], description="CORS ExposeHeaders (--public-url)"
    )

    @validator("auth_type")
    def is_valid_auth_type(cls, v):
        valid_auth_types = ["NONE", "AWS"]
        if v not in valid_auth_types:
            raise ValueError(f"auth_type must be one of {', '.join(valid_auth_types)}")
        return v
