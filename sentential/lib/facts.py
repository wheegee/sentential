from pathlib import Path, PosixPath
import boto3
from pydantic import BaseModel, validator
from typing import Optional, Any
from sentential.lib.clients import clients
from sentential.lib.store import ConfigStore, SecretStore


class Paths(BaseModel):
    root: PosixPath
    src: PosixPath
    sentential_file: PosixPath
    dockerfile: PosixPath
    wrapper: PosixPath
    policy: PosixPath


class Facts(BaseModel):
    repository_name: str
    runtime: Optional[str]
    region: str = boto3.session.Session().region_name
    path: Optional[Paths]
    account_id: str = clients.sts.get_caller_identity().get("Account")
    kms_key_alias: str = "aws/ssm"
    kms_key_id: Optional[str]
    repository_url: Optional[str]
    registry_url: Optional[str]
    config: Optional[Any]

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

    @validator("config", always=True)
    def assemble_config(cls, v, values) -> Any:
        return ConfigStore(values["repository_name"]).parameters()

    @validator("path", always=True)
    def assemble_path(cls, v, values) -> str:
        root = Path(".")
        return Paths(
            root=root,
            src=Path(f"{root}/src"),
            sentential_file=Path(f"{root}/sentential.yml"),
            dockerfile=Path(f"{root}/Dockerfile"),
            wrapper=Path(f"{root}/wrapper.sh"),
            policy=Path(f"{root}/policy.json"),
        )
