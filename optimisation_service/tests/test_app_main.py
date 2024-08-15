from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestMain:
    def test_read_main(self):
        response = client.get("/")
        assert response.status_code == 200
