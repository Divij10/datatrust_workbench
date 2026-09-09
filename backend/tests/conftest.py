import os

import pytest
from fastapi.testclient import TestClient

os.environ["DATATRUST_ENVIRONMENT"] = "test"
os.environ["DATATRUST_MAX_UPLOAD_SIZE_BYTES"] = "1024"
os.environ["DATATRUST_MAX_ROWS"] = "10"


@pytest.fixture
def client() -> TestClient:
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
