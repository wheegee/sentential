from pathlib import PosixPath, Path
from typing import List
from pydantic import BaseModel, Field, Extra
from typing import Annotated
from sentential.lib.shapes.aws import AWSPolicyDocument
from typing import Annotated

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

class Provision(BaseModel):
    storage: Annotated[int, Field(description="ephemeral storage (gb)")] = 512
    memory: Annotated[int, Field(description="allocated memory (mb)")] = 128
    timeout: Annotated[int, Field(description="timeout (s)")] = 3
    subnet_ids: Annotated[List[str], Field(description="subnet ids")] = []
    security_group_ids: Annotated[List[str], Field(description="security group ids")] = []

class Config:
    extra = Extra.forbid