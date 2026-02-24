"""
test_health.py – Test dell'endpoint GET /health.
"""

import requests
from conftest import BASE_URL


class TestHealth:
    """Verifica che il server sia raggiungibile e risponda correttamente."""

    def test_health_status_code(self):
        """GET /health deve restituire 200 OK."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200

    def test_health_response_body(self):
        """GET /health deve restituire {"status": "ok"}."""
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        assert data == {"status": "ok"}

    def test_health_content_type(self):
        """GET /health deve restituire JSON."""
        response = requests.get(f"{BASE_URL}/health")
        assert "application/json" in response.headers.get("Content-Type", "")
