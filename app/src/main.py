import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from mangum import Mangum
from datetime import datetime

from config.env import API_DESCRIPTION, API_NAME, API_VERSION
from config.ssm import ssm

api = FastAPI(
    title=API_NAME,
    version=API_VERSION,
    description=API_DESCRIPTION,
)

origins = [
    "http://localhost",
    "http://localhost:8080",
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/")
def root():
    return {"route": "/"}

@api.get("/time")
def time():
    return {"time": datetime.now(), "route": "/time"}

@api.get("/config")
def config():
    return {"config": ssm(), "route": "/config"}

# Override fastapi's internal naming scheme for OpenAPI v3's operation_id property
# source: https://fastapi.tiangolo.com/advanced/path-operation-advanced-configuration/#using-the-path-operation-function-name-as-the-operationid

for route in api.routes:
    if isinstance(route, APIRoute):
        route.operation_id = route.name

if os.getenv("LAMBDA_TASK_ROOT") is not None:
    handler = Mangum(api)
elif __name__ == "__main__":
    uvicorn.run("main:api", host="0.0.0.0", port=8080, reload=True)
