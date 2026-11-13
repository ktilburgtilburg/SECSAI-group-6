import importlib
import json
import socket
from pathlib import Path

import pytest

URL_CASES = json.loads((Path(__file__).parent / "fixtures" / "urls.json").read_text())


@pytest.fixture(autouse=True)
def block_network(monkeypatch, request):
    """URL fixtures are strings; any attempt to contact them must fail."""
    if request.node.get_closest_marker("integration"):
        if not request.config.getoption("--system-url"):
            pytest.skip("requires --system-url for the composed system")
        return

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
def client(api_module, monkeypatch, tmp_path):
    request_db_path = tmp_path / "api.db"
    # API contract tests are independent of the ignored trained-model artifact.
    # The speed benchmark deliberately uses the real model instead.
    from secsai_group_6.backend.stub_model import predict

    monkeypatch.setattr(api_module, "rpc_assess", lambda url: (predict(url), "unit"))
    monkeypatch.setattr(api_module, "queue_is_up", lambda: True)
    monkeypatch.setitem(api_module.app.config, "DB_PATH", request_db_path)
    monkeypatch.setitem(api_module.app.config, "TESTING", True)
    with api_module.app.test_client() as client:
        yield client


def pytest_addoption(parser):
    parser.addoption("--system-url", default=None)


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: live composed system tests")
