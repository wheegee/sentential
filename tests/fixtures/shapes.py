from sentential.support.shaper import Shaper, List, Field

class Arg(Shaper):
    REQUIRED_ARG: str = Field(description="required argument")
    OPTIONAL_ARG: str = Field(default="hello", description="optional argument")
    list_arg: str = Field(default=["one", "two", "four"], description="optional list argument")

class Env(Shaper):
    # REQUIRED_ENV: str = Field(description="required environment variable")
    OPTIONAL_ENV: str = Field(default="hello", description="optional environment variable")
    list_env: str = Field(default=["one", "two", "four"], description="optional list envirnment variable")

