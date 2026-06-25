"""
test_api_pcs.py — Tests para el CRUD de PCs en el servidor central
"""

import pytest
from fastapi.testclient import TestClient
from servidor.config import settings

AUTH_HEADERS = {"Authorization": f"Bearer {settings.secret_key}"}


class TestRegisterPC:
    def test_register_pc_ok(self, client: TestClient, sample_pc_data: dict):
        """Registrar una PC válida debe retornar 201 con los datos correctos."""
        resp = client.post("/api/pcs", json=sample_pc_data)

        assert resp.status_code == 201
        data = resp.json()
        assert data["ip"] == sample_pc_data["ip"]
        assert data["name"] == sample_pc_data["name"]
        assert data["status"] == "unknown"
        assert data["id"] is not None

    def test_register_pc_duplicate_ip(self, client: TestClient, sample_pc_data: dict):
        """Registrar una IP ya existente debe retornar 409."""
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
        client.post("/api/pcs", json=sample_pc_data)

        resp = client.get("/api/pcs")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["ip"] == sample_pc_data["ip"]

    def test_get_single_pc(self, client: TestClient, sample_pc_data: dict):
        """GET /api/pcs/{id} debe retornar la PC correcta."""
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


class TestAgentEndpoints:
    def test_agent_push_new_pc(self, client: TestClient):
        payload = {
            "agent_id": "agent-test-123",
            "ip": "192.168.1.150",
            "name": "PC-Agent-01",
            "hostname": "agent-host",
            "os": "Linux 6.1",
            "metrics": {
                "cpu": {"percent": 15.5},
                "memory": {"percent": 45.0, "used_gb": 4.0, "total_gb": 8.0},
                "disk": {"/": {"percent": 30.0}},
                "processes": {"total": 120},
                "network": {"connections": 15},
                "uptime_seconds": 3600
            }
        }
        resp = client.post("/api/agent/push", json=payload, headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_agent_push_invalid_payload(self, client: TestClient):
        resp = client.post("/api/agent/push", json={"ip": "192.168.1.150"}, headers=AUTH_HEADERS)
        assert resp.status_code == 400

    def test_agent_command_result(self, client: TestClient):
        resp = client.post("/api/agent/command_result", json={
            "command_id": "test-cmd-id",
            "result": {"stdout": "hello", "exit_code": 0}
        }, headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestPCMetricsAndEvents:
    def test_get_pc_metrics_empty(self, client: TestClient):
        resp = client.get("/api/pcs/999/metrics")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_pc_events_empty(self, client: TestClient):
        resp = client.get("/api/pcs/999/events")
        assert resp.status_code == 200
        assert resp.json() == []


class TestPCExecuteCommand:
    def test_execute_on_nonexistent_pc(self, client: TestClient):
        resp = client.post("/api/pcs/9999/execute", json={"command": "dir"}, headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_execute_on_offline_pc(self, client: TestClient, sample_pc_data: dict):
        created = client.post("/api/pcs", json=sample_pc_data).json()
        resp = client.post(f"/api/pcs/{created['id']}/execute", json={"command": "dir"}, headers=AUTH_HEADERS)
        assert resp.status_code == 503

    def test_execute_empty_command(self, client: TestClient, sample_pc_data: dict):
        payload = {
            "agent_id": "agent-test-456",
            "ip": sample_pc_data["ip"],
            "name": sample_pc_data["name"],
            "metrics": {"cpu": {"percent": 10.0}}
        }
        client.post("/api/agent/push", json=payload, headers=AUTH_HEADERS)

        pcs = client.get("/api/pcs").json()
        pc_id = [p["id"] for p in pcs if p["ip"] == sample_pc_data["ip"]][0]

        resp = client.post(f"/api/pcs/{pc_id}/execute", json={"command": ""}, headers=AUTH_HEADERS)
        assert resp.status_code == 400


class TestExportExcel:
    def test_export_excel(self, client: TestClient):
        resp = client.get("/api/export/excel")
        assert resp.status_code == 200
        # Verificar que es una respuesta de archivo (por ejemplo, headers de adjunto o content-type)
        assert "content-disposition" in resp.headers
        assert "filename" in resp.headers["content-disposition"]


class TestConnectionManager:
    @pytest.mark.anyio
    async def test_connection_manager(self):
        """Verifica que el ConnectionManager registre, elimine y transmita a WebSockets correctamente."""
        from unittest.mock import AsyncMock, MagicMock

        from main import manager

        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()

        # Test connect
        await manager.connect(ws)
        assert ws in manager.active

        # Test broadcast
        await manager.broadcast({"type": "test_msg"})
        ws.send_json.assert_called_with({"type": "test_msg"})

        # Test disconnect
        manager.disconnect(ws)
        assert ws not in manager.active


