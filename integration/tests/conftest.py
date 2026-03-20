import pytest
from code import data_store

@pytest.fixture(autouse=True)
def reset_store():
    data_store.reset_all()
    yield