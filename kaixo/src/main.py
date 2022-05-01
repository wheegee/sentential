import uvicorn
import os

from config.env import API_NAME, API_VERSION
from config.ssm import auth0_config

from auth0.v3.authentication.token_verifier import TokenVerifier, AsymmetricSignatureVerifier, TokenValidationError

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer

from mangum import Mangum

token_auth_scheme = HTTPBearer()
sv = AsymmetricSignatureVerifier(auth0_config.jwks_endpoint)

def authorize(token: str = Depends(token_auth_scheme)):
    tv = TokenVerifier(signature_verifier=sv, issuer=auth0_config.issuer, audience=auth0_config.audience)
    try:
        return tv.verify(token.credentials)
    except TokenValidationError:
        raise HTTPException(status_code=400, detail="invalid bearer token")

api = FastAPI(
    title=API_NAME,
    version=API_VERSION,
    dependencies=[Depends(authorize)],
    debug=True
)

@api.get("/")
def get_root():
    return { "root": "route" }

@api.get("/private")
def get_private():
    return auth0_config

if os.getenv('LAMBDA_TASK_ROOT') is not None:
    handler = Mangum(api)
elif __name__ == "__main__":
    uvicorn.run("main:api", host="0.0.0.0", port=8080, reload=True)