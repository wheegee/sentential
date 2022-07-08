from pydantic import BaseModel, validator
from pathlib import Path, PosixPath
from typing import Optional
import boto3


class PathConfig(BaseModel):
    root: PosixPath
    src: PosixPath
    dockerfile: PosixPath
    wrapper: PosixPath
    policy: PosixPath


class Config(BaseModel):
    repository_name: str
    runtime: Optional[str]
    path: Optional[PathConfig]
    region: str = boto3.session.Session().region_name
    account_id: str = boto3.client("sts").get_caller_identity().get("Account")
    kms_key_alias: str = "aws/ssm"
    kms_key_id: Optional[str]
    repository_url: Optional[str]
    registry_url: Optional[str]

    @validator("kms_key_id", always=True)
    def lookup_kms_key_id(cls, v, values) -> str:
        return [
            ssm_key["TargetKeyId"]
            for ssm_key in boto3.client("kms").list_aliases()["Aliases"]
            if values["kms_key_alias"] in ssm_key["AliasName"]
        ][0]

    @validator("repository_url", always=True)
    def assemble_repository_url(cls, v, values) -> str:
        return f"{values['account_id']}.dkr.ecr.{values['region']}.amazonaws.com/{values['repository_name']}"

    @validator("registry_url", always=True)
    def assemble_registry_url(cls, v, values) -> str:
        return f"{values['account_id']}.dkr.ecr.{values['region']}.amazonaws.com"

    @validator("path", always=True)
    def assemble_path(cls, v, values) -> str:
        root = Path(f"lambdas/{values['repository_name']}")
        return PathConfig(
            root=root,
            src=Path(f"{root}/src"),
            dockerfile=Path(f"{root}/Dockerfile"),
            wrapper=Path(f"{root}/wrapper.sh"),
            policy=Path(f"{root}/policy.json"),
        )
