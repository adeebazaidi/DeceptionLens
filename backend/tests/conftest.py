"""
Pytest configuration — isolates tests from real case data.

Points the database and evidence storage at a throwaway temp directory
before any application module is imported.
"""

import os
import shutil
import tempfile
from pathlib import Path

_TEST_DIR = Path(tempfile.mkdtemp(prefix="deceptionlens_test_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_DIR / 'test.db').as_posix()}"
os.environ["EVIDENCE_STORAGE_DIR"] = str(_TEST_DIR / "evidence_storage")


def pytest_sessionfinish(session, exitstatus):
    from database.connection import engine

    engine.dispose()
    shutil.rmtree(_TEST_DIR, ignore_errors=True)
