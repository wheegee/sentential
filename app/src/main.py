import uvicorn
import os
from fastapi import FastAPI
from mangum import Mangum
from datetime import datetime

from config.env import API_DESCRIPTION, API_NAME, API_VERSION
from config.ssm import ssm

api = FastAPI(
    title=API_NAME,
    version=API_VERSION,
    description=API_DESCRIPTION,
)


@api.get("/")
def get_root():
    return {"route": "/"}


@api.get("/time")
def get_private():
    return {"time": datetime.now(), "route": "/time"}


@api.get("/config")
def get_config():
    return {"config": ssm(), "route": "/config"}


if os.getenv("LAMBDA_TASK_ROOT") is not None:
    handler = Mangum(api)
elif __name__ == "__main__":
    uvicorn.run("main:api", host="0.0.0.0", port=8080, reload=True)
