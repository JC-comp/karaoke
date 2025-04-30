import os
import pytest
import shutil

@pytest.fixture(autouse=True)
def global_fixture(tmp_path):
    """
    Fixture to set the temporary directory for tests.
    """
    from karaoke.utils.config import Config
    config = Config()
    config.work_dir = str(tmp_path)
    config.media_path = str(tmp_path)

@pytest.fixture
def prepare_data(tmpdir, request):
    """
    Fixture to prepare data for tests. Copies static files within the request module's directory
    to the temporary directory.
    """
    testname = request.module.__file__
    datadir = os.path.join(os.path.dirname(testname), 'static')
    shutil.copytree(datadir, tmpdir, dirs_exist_ok=True, ignore=shutil.ignore_patterns('hidden'))
    return tmpdir

@pytest.fixture
def prepare_hidden_data(request, tmpdir):
    """
    Fixture to prepare data for tests. Copies static files within the request module's directory
    to the temporary directory.
    """
    testname = request.module.__file__
    datadir = os.path.join(os.path.dirname(testname), 'static', 'hidden')
    for f in request.param:
        src = os.path.join(datadir, f)
        if not os.path.exists(src):
            raise FileNotFoundError(f"File {src} does not exist")
        dst = os.path.join(tmpdir, os.path.basename(src))
        shutil.copy(src, dst)
    return tmpdir