from sentential.lib.shapes import StoreModel
from pydantic import Field

class Args(StoreModel):
    required_arg: int = Field(description="required")
    optional_arg: str = Field(default="default_value", description="optional")


class Envs(StoreModel):
    required_env: int = Field(description="required")
    optional_env: str = Field(default="default_value", description="optional")


class Secrets(StoreModel):
    required_secret: int = Field(description="required")
    optional_secret: str = Field(default="default_value", description="optional")


class Tags(StoreModel):
    required_tag: int = Field(description="required")
    optional_tag: str = Field(default="default_value", description="optional")
