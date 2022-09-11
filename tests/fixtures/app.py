from fastapi import FastAPI
from mangum import Mangum
from os import environ

app = FastAPI()


@app.get("/")
def get_envar():
    return dict(environ)


handler = Mangum(app, lifespan="off")
