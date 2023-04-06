from sentential.lib.shapes import BaseModel, BaseModelStrict
from pydantic import Field


class Args(BaseModelStrict):
    required_arg: int = Field(description="required")
    optional_arg: str = Field(default="default_value", description="optional")


class Envs(BaseModelStrict):
    required_env: int = Field(description="required")
    optional_env: str = Field(default="default_value", description="optional")


class Secrets(BaseModelStrict):
    required_secret: int = Field(description="required")
    optional_secret: str = Field(default="default_value", description="optional")


class Tags(BaseModelStrict):
    required_tag: int = Field(description="required")
    optional_tag: str = Field(default="default_value", description="optional")
