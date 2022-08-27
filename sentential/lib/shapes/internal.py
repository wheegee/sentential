from pathlib import PosixPath, Path
from typing import List
from pydantic import BaseModel, Field
from sentential.lib.shapes.aws import AWSPolicyDocument
from sentential.support.shaper import Shaper

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
# Internally Defined Shapes
#


class Provision(Shaper):
    storage: int = Field(default=512, description="ephemeral storage (mb)")
    memory: int = Field(default=128, description="allocated memory (mb)")
    timeout: int = Field(default=3, description="timeout (s)")
    subnet_ids: List[str] = Field(default=[], description="subnet ids")
    security_group_ids: List[str] = Field(default=[], description="security group ids")
