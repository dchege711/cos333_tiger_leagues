"""
conftest.py

https://docs.pytest.org/en/latest/fixture.html
"""

import sys
sys.path.insert(0, "../..")

import pytest
from dev_scripts.clean_database import clean_database

@pytest.fixture(scope="function")
def cleanup():
    yield clean_database()
    clean_database()
