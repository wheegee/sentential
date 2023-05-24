from sentential.lib.shapes import StoreModel
from pydantic import Field


class Args(StoreModel):
    required_arg: int = Field(default=123, description="required")
    optional_arg: str = Field(default="one, two, three", description="optional")


class Envs(StoreModel):
    required_env: int = Field(default=123, description="required")
    optional_env: str = Field(default="one, two, three", description="optional")


class Secrets(StoreModel):
    required_secret: int = Field(default=123, description="required")
    optional_secret: str = Field(default="one, two, three", description="optional")


class Tags(StoreModel):
    required_tag: int = Field(default=123, description="required")
    optional_tag: str = Field(default="one, two, three", description="optional")
