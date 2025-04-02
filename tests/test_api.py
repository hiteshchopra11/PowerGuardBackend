from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to PowerGuard Backend API"}

def test_device_data_validation():
    test_data = {
        "device_id": "test_device_001",
        "timestamp": datetime.now().isoformat(),
        "power_consumption": 2.5,
        "temperature": 25.5,
        "status": "active"
    }
    response = client.post("/api/device-data", json=test_data)
    assert response.status_code == 200  # or 201 depending on your implementation 