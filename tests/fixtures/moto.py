import pytest
from moto.server import ThreadedMotoServer


@pytest.fixture(scope="class")
def moto():
    server = ThreadedMotoServer()
    server.start()
    yield
    server.stop()
