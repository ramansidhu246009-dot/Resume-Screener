from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_empty_job_description():
    response = client.post(
        "/rank",
        data={"job_description": ""},
        files=[("resumes", ("test.pdf", b"dummy content", "application/pdf"))]
    )
    assert response.status_code == 422
