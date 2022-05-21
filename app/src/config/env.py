import os

API_NAME = os.getenv(
    "API_NAME", default="app"
)  # Don't really know how this should ultimately be defined.
API_VERSION = os.getenv(
    "API_VERSION", default="defined by `ENV API_VERSION=` in Dockerfile"
)
API_DESCRIPTION = os.getenv(
    "API_DESCRIPTION", default="defined by `ENV API_DESCRIPTION=` in Dockerfile"
)
AWS_REGION = os.getenv("AWS_REGION", default="us-west-2")
