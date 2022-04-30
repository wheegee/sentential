from config.env import API_NAME, API_VERSION
from config.ssm import api_config

import uvicorn
import os

from auth0.v3.authentication.token_verifier import TokenVerifier, AsymmetricSignatureVerifier, TokenValidationError

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware

from mangum import Mangum

token_auth_scheme = HTTPBearer()
sv = AsymmetricSignatureVerifier(api_config.jwks_endpoint)

def authorize(token: str = Depends(token_auth_scheme)):
    tv = TokenVerifier(signature_verifier=sv, issuer=api_config.issuer, audience=api_config.audience)
    try:
        return tv.verify(token.credentials)
    except TokenValidationError:
        raise HTTPException(status_code=400, detail="invalid bearer token")

api = FastAPI(
    title=API_NAME,
    version=API_VERSION,
    dependencies=[Depends(authorize)]
)

origins = [
    "http://localhost",
    "http://localhost:8080",
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/env")
def get_env():
    return api_config

if os.getenv('LAMBDA_TASK_ROOT') is not None:
    handler = Mangum(api)
elif __name__ == "__main__":
    uvicorn.run("main:api", host="0.0.0.0", port=8000, reload=True)
