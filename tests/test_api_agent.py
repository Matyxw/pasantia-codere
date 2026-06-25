"""
test_api_agent.py — Tests del flujo push del agente
"""

from fastapi.testclient import TestClient

from servidor.config import settings
AUTH_HEADERS = {"Authorization": f"Bearer {settings.secret_key}"}


class TestAgentPush:
    def test_push_registers_pc(self, client: TestClient):
        payload = {
            "agent_id": "agent-test-001",
            "ip": "10.0.0.50",
            "name": "PC-Agent",
            "hostname": "PC-Agent",
            "os": "Windows 11",
            "metrics": {
                "cpu": {"percent": 12.5},
                "memory": {"percent": 40.0, "used_gb": 4.0, "total_gb": 10.0},
                "disk": {"C:\\": {"percent": 55.0}},
                "processes": {"total": 120},
                "network": {"connections": 30},
                "uptime_seconds": 3600,
            },
        }

        resp = client.post("/api/agent/push", json=payload, headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["pending_commands"] == []

        pcs = client.get("/api/pcs").json()
        assert len(pcs) == 1
        assert pcs[0]["ip"] == "10.0.0.50"
        assert pcs[0]["status"] == "online"

    def test_push_requires_auth(self, client: TestClient):
        payload = {
            "agent_id": "agent-test-002",
            "ip": "10.0.0.51",
            "metrics": {"cpu": {"percent": 1.0}},
        }
        resp = client.post("/api/agent/push", json=payload)
        assert resp.status_code in (401, 403)

    def test_push_missing_fields(self, client: TestClient):
        resp = client.post(
            "/api/agent/push",
            json={"agent_id": "x", "ip": "1.1.1.1"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 400

    def test_command_result_roundtrip(self, client: TestClient):
        payload = {
            "agent_id": "agent-test-003",
            "ip": "10.0.0.52",
            "name": "PC-Cmd",
            "metrics": {
                "cpu": {"percent": 5.0},
                "memory": {"percent": 20.0, "used_gb": 2.0, "total_gb": 8.0},
                "disk": {},
                "processes": {"total": 50},
                "network": {"connections": 10},
                "uptime_seconds": 100,
            },
        }
        client.post("/api/agent/push", json=payload, headers=AUTH_HEADERS)

        result_payload = {
            "command_id": "cmd-123",
            "result": {"stdout": "ok", "exit_code": 0},
        }
        resp = client.post(
            "/api/agent/command_result",
            json=result_payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestExportExcel:
    def test_export_excel_empty(self, client: TestClient):
        resp = client.get("/api/export/excel")
        assert resp.status_code == 200
        assert (
            resp.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_export_excel_with_pc(self, client: TestClient):
        payload = {
            "agent_id": "agent-export-001",
            "ip": "10.0.0.60",
            "name": "PC-Export",
            "hostname": "PC-Export",
            "os": "Windows 10",
            "metrics": {
                "cpu": {"percent": 22.0},
                "memory": {"percent": 50.0, "used_gb": 5.0, "total_gb": 10.0},
                "disk": {"C:\\": {"percent": 70.0}},
                "processes": {"total": 80},
                "network": {"connections": 15},
                "uptime_seconds": 500,
                "system": {"architecture": "64bit", "processor": "Intel"},
            },
        }
        client.post("/api/agent/push", json=payload, headers=AUTH_HEADERS)

        resp = client.get("/api/export/excel?ip=10.0.0.60")
        assert resp.status_code == 200
        assert len(resp.content) > 1000

    def test_get_metrics_after_push(self, client: TestClient):
        payload = {
            "agent_id": "agent-metrics-001",
            "ip": "10.0.0.61",
            "name": "PC-Metrics",
            "metrics": {
                "cpu": {"percent": 8.0},
                "memory": {"percent": 30.0, "used_gb": 3.0, "total_gb": 8.0},
                "disk": {"C:\\": {"percent": 40.0}},
                "processes": {"total": 60},
                "network": {"connections": 12},
                "uptime_seconds": 200,
            },
        }
        client.post("/api/agent/push", json=payload, headers=AUTH_HEADERS)
        pc_id = client.get("/api/pcs").json()[0]["id"]

        resp = client.get(f"/api/pcs/{pc_id}/metrics")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["cpu"] == 8.0
