from fastapi import FastAPI
from mangum import Mangum
from os import environ

app = FastAPI()


@app.get("/")
def get_envar(key: str):
    return {f"{key}": environ[key]}


handler = Mangum(app, lifespan="off")
