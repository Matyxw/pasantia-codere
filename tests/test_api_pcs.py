"""
test_api_pcs.py — Tests para el CRUD de PCs en el servidor central
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestRegisterPC:
    def test_register_pc_ok(self, client: TestClient, sample_pc_data: dict):
        """Registrar una PC válida debe retornar 201 con los datos correctos."""
        with patch("servidor.main.requests.get", side_effect=ConnectionError):
            resp = client.post("/api/pcs", json=sample_pc_data)

        assert resp.status_code == 201
        data = resp.json()
        assert data["ip"] == sample_pc_data["ip"]
        assert data["name"] == sample_pc_data["name"]
        assert data["status"] == "unknown"
        assert data["id"] is not None

    def test_register_pc_duplicate_ip(self, client: TestClient, sample_pc_data: dict):
        """Registrar una IP ya existente debe retornar 409."""
        with patch("servidor.main.requests.get", side_effect=ConnectionError):
            client.post("/api/pcs", json=sample_pc_data)
            resp = client.post("/api/pcs", json=sample_pc_data)

        assert resp.status_code == 409

    def test_register_pc_missing_ip(self, client: TestClient):
        """Registrar sin IP debe retornar 400."""
        resp = client.post("/api/pcs", json={"name": "PC-Sin-IP"})
        assert resp.status_code == 400

    def test_register_pc_missing_name(self, client: TestClient):
        """Registrar sin nombre debe retornar 400."""
        resp = client.post("/api/pcs", json={"ip": "192.168.1.1"})
        assert resp.status_code == 400


class TestGetPCs:
    def test_list_pcs_empty(self, client: TestClient):
        """Sin PCs registradas, debe retornar lista vacía."""
        resp = client.get("/api/pcs")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_pcs_after_register(self, client: TestClient, sample_pc_data: dict):
        """Después de registrar, debe aparecer en la lista."""
        with patch("servidor.main.requests.get", side_effect=ConnectionError):
            client.post("/api/pcs", json=sample_pc_data)

        resp = client.get("/api/pcs")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["ip"] == sample_pc_data["ip"]

    def test_get_single_pc(self, client: TestClient, sample_pc_data: dict):
        """GET /api/pcs/{id} debe retornar la PC correcta."""
        with patch("servidor.main.requests.get", side_effect=ConnectionError):
            created = client.post("/api/pcs", json=sample_pc_data).json()

        resp = client.get(f"/api/pcs/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["ip"] == sample_pc_data["ip"]

    def test_get_pc_not_found(self, client: TestClient):
        """GET de ID inexistente debe retornar 404."""
        resp = client.get("/api/pcs/99999")
        assert resp.status_code == 404


class TestDeletePC:
    def test_delete_pc(self, client: TestClient, sample_pc_data: dict):
        """Eliminar una PC debe retornar 200 y quitarla de la lista."""
        with patch("servidor.main.requests.get", side_effect=ConnectionError):
            created = client.post("/api/pcs", json=sample_pc_data).json()

        resp = client.delete(f"/api/pcs/{created['id']}")
        assert resp.status_code == 200

        # Verificar que ya no existe
        resp2 = client.get(f"/api/pcs/{created['id']}")
        assert resp2.status_code == 404

    def test_delete_pc_not_found(self, client: TestClient):
        """Eliminar ID inexistente debe retornar 404."""
        resp = client.delete("/api/pcs/99999")
        assert resp.status_code == 404


class TestStats:
    def test_stats_empty(self, client: TestClient):
        """Stats sin PCs debe mostrar todos en 0."""
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["online"] == 0
        assert data["offline"] == 0


class TestEvents:
    def test_events_empty(self, client: TestClient):
        """Sin eventos, retornar lista vacía."""
        resp = client.get("/api/events")
        assert resp.status_code == 200
        assert resp.json() == []
