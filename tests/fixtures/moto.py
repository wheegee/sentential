import pytest
from moto.server import ThreadedMotoServer
import requests


@pytest.fixture(scope="class")
def moto():
    server = ThreadedMotoServer()
    server.start()
    yield
    requests.post("http://localhost:5000/moto-api/reset")
    server.stop()
