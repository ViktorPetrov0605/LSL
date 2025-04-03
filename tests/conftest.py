import pytest

@pytest.fixture(autouse=True)
def no_subprocess(monkeypatch):
    """Mock subprocess to prevent actual Docker calls during tests."""
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: None)
