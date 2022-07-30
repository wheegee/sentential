#
# Spec
#

from pathlib import PosixPath
from pydantic import BaseModel
from sentential.lib.shapes.aws import AWSPolicyDocument


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
    sentential_file: PosixPath
    dockerfile: PosixPath
    wrapper: PosixPath
    policy: PosixPath
