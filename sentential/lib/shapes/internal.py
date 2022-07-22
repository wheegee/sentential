#
# Spec
#

from pydantic import BaseModel
from sentential.lib.shapes.aws import AWSPolicyDocument

class Spec(BaseModel):
    prefix: str
    policy: AWSPolicyDocument
    role_name: str
    policy_name: str