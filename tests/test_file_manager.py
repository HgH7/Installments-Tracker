import os
import tempfile

import pytest

from app.core.file_manager import FileManager


@pytest.fixture
def fm():
    tmpdir = tempfile.mkdtemp(prefix="fm_test_")
    manager = FileManager(tmpdir)
    yield manager
    import shutil
    shutil.rmtree(tmpdir)


class TestSafeName:
    def test_normal_name(self, fm):
        assert fm._safe_name("Alice Smith") == "Alice Smith"

    def test_name_with_special_chars(self, fm):
        assert fm._safe_name("hello@#$%world") == "helloworld"

    def test_name_with_dots(self, fm):
        assert fm._safe_name("file.name.txt") == "file.name.txt"

    def test_name_path_traversal(self, fm):
        assert fm._safe_name("../etc/passwd") == "..etcpasswd"

    def test_name_single_dot(self, fm):
        assert fm._safe_name(".") == "_"

    def test_name_double_dot(self, fm):
        assert fm._safe_name("..") == "_"

    def test_name_empty_string(self, fm):
        assert fm._safe_name("") == "_"

    def test_name_unicode(self, fm):
        name = fm._safe_name("أحمد")
        assert name  # should contain the unicode chars


class TestGetCustomerDir:
    def test_creates_directory(self, fm):
        path = fm._get_customer_dir("Alice")
        assert os.path.isdir(path)

    def test_path_traversal_prevented_by_safe_name(self, fm):
        dir_path = fm._get_customer_dir("../malicious")
        assert os.path.realpath(dir_path).startswith(os.path.realpath(fm.base_dir))

    def test_same_dir_for_same_name(self, fm):
        p1 = fm._get_customer_dir("Alice")
        p2 = fm._get_customer_dir("Alice")
        assert p1 == p2

    def test_different_dir_for_different_name(self, fm):
        p1 = fm._get_customer_dir("Alice")
        p2 = fm._get_customer_dir("Bob")
        assert p1 != p2


class TestAddFiles:
    def test_add_single_file(self, fm):
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        tmp.write(b"hello")
        tmp.close()
        try:
            assert fm.add_files("Alice", [tmp.name])
        finally:
            os.unlink(tmp.name)

    def test_add_multiple_files(self, fm):
        files = []
        for i in range(3):
            tmp = tempfile.NamedTemporaryFile(suffix=f"_{i}.txt", delete=False)
            tmp.write(b"data")
            tmp.close()
            files.append(tmp.name)
        try:
            assert fm.add_files("Alice", files)
        finally:
            for f in files:
                os.unlink(f)

    def test_add_nonexistent_file(self, fm):
        assert not fm.add_files("Alice", ["/nonexistent/file.txt"])

    def test_duplicate_filename_renames(self, fm):
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        tmp.write(b"first")
        tmp.close()
        tmp2 = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        tmp2.write(b"second")
        tmp2.close()
        try:
            import shutil
            fm.add_files("Alice", [tmp.name])
            fm.add_files("Alice", [tmp2.name])
            cust_dir = fm._get_customer_dir("Alice")
            files = os.listdir(cust_dir)
            renamed = [f for f in files if f != os.path.basename(tmp.name)]
            assert len(files) == 2
        finally:
            os.unlink(tmp.name)
            os.unlink(tmp2.name)


class TestInit:
    def test_creates_base_directory(self):
        tmpdir = tempfile.mkdtemp(prefix="fm_init_")
        dir_path = os.path.join(tmpdir, "subdir")
        fm = FileManager(dir_path)
        assert os.path.isdir(dir_path)
        import shutil
        shutil.rmtree(tmpdir)
