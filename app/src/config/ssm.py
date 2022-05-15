from aws_lambda_powertools.utilities import parameters
from botocore.config import Config
from base64 import b64decode
from pydantic import BaseModel

from config.env import AWS_REGION, API_NAME

config = Config(region_name=AWS_REGION)
ssm_provider = parameters.SSMProvider(config=config)
ssm_params = ssm_provider.get_multiple(f"/{API_NAME}/", decrypt=True)

# Levarage this to give meaningful validation / requirements of SSM parameters.
# Currently it doesn't do much good.


class Auth0Config(BaseModel):
    domain: str
    audience: str
    issuer: str
    jwks_endpoint: str

class RDSConfig(BaseModel):
    instance: str
    user: str
    root_cert: str
    database: str


auth0_config = Auth0Config(
    domain=ssm_params["domain"],
    audience=ssm_params["audience"],
    issuer='{}/'.format(ssm_params["domain"]),
    jwks_endpoint='{}/.well-known/jwks.json'.format(ssm_params["domain"])
)

rds_config = RDSConfig(
    instance=ssm_params["db_instance"],
    user=ssm_params["db_user"],
    root_cert=b64decode(ssm_params["db_root_cert"]),
    database=ssm_params["db_name"]
)
