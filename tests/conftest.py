import multiprocessing
import pytest

from tests.fixtures.job import *
from tests.fixtures.conf import *

@pytest.fixture(scope="session", autouse=True)
def always_spawn():
    multiprocessing.set_start_method("spawn")
    