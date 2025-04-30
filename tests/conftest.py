import multiprocessing
import pytest

from tests.fixtures.job import *
from tests.fixtures.conf import *

def pytest_addoption(parser):
    parser.addoption(
        "--gpt-server", action="store_true", help="Run tests with GPT server online"
    )

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "gpt_server: mark test to run only if the GPT server is available"
    )

def pytest_collection_modifyitems(config, items):
    if config.getoption("--gpt-server"):
        # --gpt-server option was not given, skip tests with gpt_server marker
        return
    # --gpt-server option was given, skip tests without gpt_server marker
    skip_gpt_server = pytest.mark.skip(reason="need --gpt-server option to run")
    for item in items:
        if "gpt_server" in item.keywords:
            item.add_marker(skip_gpt_server)

@pytest.fixture(scope="session", autouse=True)
def always_spawn():
    multiprocessing.set_start_method("spawn")
    