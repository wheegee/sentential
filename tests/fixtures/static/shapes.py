from sentential.support.shaper import Shaper, List, Field

class Args(Shaper):
    required_arg: str = Field(description="required")
    optional_arg: str = Field(default="default_value", description="optional")

class Envs(Shaper):
    required_env: str = Field(description="required")
    optional_env: str = Field(default="default_value", description="optional")