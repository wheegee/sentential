#
# Spec
#

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class AWSPolicyStatement(BaseModel):
    Effect: str
    Action: Union[str, List[str]]
    Principal: Optional[dict]
    Resource: Optional[Union[str, List[str]]]
    Condition: Optional[dict]


class AWSPolicyDocument(BaseModel):
    Version: str = "2012-10-17"
    Statement: List[AWSPolicyStatement]


class Spec(BaseModel):
    prefix: str
    policy: AWSPolicyDocument
    role_name: str
    policy_name: str
