import importlib
import json
import socket
from pathlib import Path

import pytest

URL_CASES = json.loads((Path(__file__).parent / "fixtures" / "urls.json").read_text())


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """URL fixtures are strings; any attempt to contact them must fail."""
    def blocked(*args, **kwargs):
        raise AssertionError("Tests must not access the network")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


@pytest.fixture(params=URL_CASES, ids=[case["id"] for case in URL_CASES])
def url_case(request):
    return request.param


@pytest.fixture
def api_module():
    return importlib.import_module("secsai_group_6.backend.app")


@pytest.fixture
def client(api_module, monkeypatch):
    # API contract tests are independent of the ignored trained-model artifact.
    # The speed benchmark deliberately uses the real model instead.
    from secsai_group_6.backend.stub_model import predict

    monkeypatch.setattr(api_module, "predict", predict)
    monkeypatch.setitem(api_module.app.config, "TESTING", True)
    with api_module.app.test_client() as client:
        yield client
