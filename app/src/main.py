import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.responses import HTMLResponse

from mangum import Mangum
from datetime import datetime

from config.env import API_DESCRIPTION, API_NAME, API_VERSION

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


@api.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Client</title>
        <script src="https://unpkg.com/swagger-client"></script>
    </head>
    <body>
        <p>open dev console and reload</p>
        <p>`client` is available in debugger</p>
        <p>example:</p>
        <pre>
        (await client.apis.default.time()).body
        </pre>

    </body>
    <script>
        new SwaggerClient('http://localhost:8080/openapi.json').then(client => { debugger })
    </script>
    </html>
    """


@api.get("/time")
def time():
    return {"time": datetime.now(), "route": "/time"}


@api.get("/hostname")
def hostname():
    return {"hostname": os.uname().nodename}


@api.post("/env")
def set_env(key: str, value: str):
    os.environ[key] = value
    return {"message": "success!"}


@api.get("/env")
def get_env(key: str):
    value = os.getenv(key)
    return {f"{key}": value}


# Override fastapi's internal naming scheme for OpenAPI v3's operation_id property
# source: https://fastapi.tiangolo.com/advanced/path-operation-advanced-configuration/#using-the-path-operation-function-name-as-the-operationid

for route in api.routes:
    if isinstance(route, APIRoute):
        route.operation_id = route.name

if os.getenv("LAMBDA_TASK_ROOT") is not None:
    handler = Mangum(api)
elif __name__ == "__main__":
    uvicorn.run("main:api", host="0.0.0.0", port=8080, reload=True)
