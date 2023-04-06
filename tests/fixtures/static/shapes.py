from sentential.lib.shapes import BaseModel, BaseModelStrict
from pydantic import Field


class Args(BaseModel):
    required_arg: int = Field(description="required")
    optional_arg: str = Field(default="default_value", description="optional")


class Envs(BaseModel):
    required_env: int = Field(description="required")
    optional_env: str = Field(default="default_value", description="optional")


class Secrets(BaseModel):
    required_secret: int = Field(description="required")
    optional_secret: str = Field(default="default_value", description="optional")


class Tags(BaseModel):
    required_tag: int = Field(description="required")
    optional_tag: str = Field(default="default_value", description="optional")
