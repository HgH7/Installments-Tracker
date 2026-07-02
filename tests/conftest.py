import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest


@pytest.fixture
def tmp_data_dir():
    with tempfile.TemporaryDirectory(prefix="it_test_") as tmpdir:
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        yield tmpdir
        os.chdir(old_cwd)
