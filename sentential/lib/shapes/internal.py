from pathlib import PosixPath, Path
from typing import List, Optional
from wsgiref.validate import validator
from pydantic import BaseModel, ValidationError, validator
from sentential.lib.shapes.aws import AWSPolicyDocument

#
# Spec
#
class Spec(BaseModel):
    prefix: str
    policy: AWSPolicyDocument
    role_name: str
    policy_name: str


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


def derive_paths(root: PosixPath = Path(".")):
    return Paths(
        root=root,
        sntl=Path(f"{root}/.sntl"),
        src=Path(f"{root}/src"),
        dockerfile=Path(f"{root}/Dockerfile"),
        wrapper=Path(f"{root}/.sntl/wrapper.sh"),
        policy=Path(f"{root}/policy.json"),
    )


#
# SNTL_META
#
class SntlMeta(BaseModel):
    repository_name: str = None
    partitions: List[str] = []

    @validator("partitions", pre=True)
    def to_list(cls, v):
        return v.split(",")
