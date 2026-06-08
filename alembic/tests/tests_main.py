from fastapi.testclient import TestClient
from main import app # Assuming your FastAPI app is in main.py

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"} # Adjust to your actual root response