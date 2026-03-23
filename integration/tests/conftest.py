import sys
import os
import pytest

# Add the 'code' directory to sys.path so that modules inside it
# (registration, data_store, etc.) can import each other by bare name.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from code import data_store   # noqa: E402  (import after sys.path patch)


@pytest.fixture(autouse=True)
def reset_store():
    data_store.reset_all()
    yield