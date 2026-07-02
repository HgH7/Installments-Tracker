import os

from app.crash_recovery import (
    SESSION_FILE,
    clear_session,
    install_global_exception_handler,
    load_session,
    save_crash_log,
    save_session,
)


class TestCrashRecovery:
    def _swap_session(self, tmp_path):
        """Redirect SESSION_FILE to a temp path for isolation."""
        self._orig = SESSION_FILE
        import app.crash_recovery as cr
        cr.SESSION_FILE = os.path.join(str(tmp_path), "session.json")

    def _restore_session(self):
        import app.crash_recovery as cr
        cr.SESSION_FILE = self._orig

    def test_save_and_load_session(self, tmp_path):
        self._swap_session(tmp_path)
        try:
            save_session("home")
            loaded = load_session()
            assert loaded == "home"
        finally:
            self._restore_session()

    def test_load_session_no_file(self, tmp_path):
        self._swap_session(tmp_path)
        try:
            result = load_session()
            assert result is None
        finally:
            self._restore_session()

    def test_clear_session(self, tmp_path):
        self._swap_session(tmp_path)
        try:
            save_session("view")
            assert load_session() == "view"
            clear_session()
            assert load_session() is None
        finally:
            self._restore_session()

    def test_save_crash_log_writes_file(self, tmp_path):
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            path = save_crash_log(ValueError, ValueError("test"), None)
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
            assert "ValueError" in content
            assert "test" in content
        finally:
            os.chdir(old_cwd)

    def test_install_exception_handler(self):
        install_global_exception_handler()
        import sys
        assert sys.excepthook.__name__ == "global_exception_handler"
