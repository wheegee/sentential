from fastapi import FastAPI
from mangum import Mangum
from os import environ

app = FastAPI()


@app.get("/{key}")
def get_envar(key: str):
    return {f"{key.upper()}": environ[key.upper()]}


handler = Mangum(app, lifespan="off")
