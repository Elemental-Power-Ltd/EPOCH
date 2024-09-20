from fastapi.testclient import TestClient

from ...app.main import app


class TestMain:
    def test_read_main(self):
        """
        Test server.
        """
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
