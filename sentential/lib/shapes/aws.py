from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime

#
# ECR
#
class ECREventDetail(BaseModel):
    """https://docs.aws.amazon.com/AmazonECR/latest/userguide/ecr-eventbridge.html"""

    result: str = "SUCCESS"
    repository_name: str = Field(alias="repository-name")
    image_digest: Optional[str] = Field(alias="image-digest")
    action_type: Optional[str] = Field(alias="action-type")
    image_tag: str = Field(alias="image-tag")


class ECREvent(BaseModel):
    """https://docs.aws.amazon.com/AmazonECR/latest/userguide/ecr-eventbridge.html"""

    version: int
    id: str
    detail_type: str = Field("ECR Image Action", const=True)
    source: str = Field("aws.ecr", const=True)
    account: str
    time: datetime = Field(datetime.now().isoformat(timespec="seconds"))
    region: str
    resources: List = []
    detail: ECREventDetail


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
            )
        ]
    )
).json(exclude_none=True)
