"""
test_agente.py — Tests para los endpoints del Agente FastAPI
"""

import os
import sys

# Agregar el directorio del agente al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agente"))

import pytest
from fastapi.testclient import TestClient

from agente import app  # type: ignore[import]


@pytest.fixture(scope="module")
def agent_client() -> TestClient:
    with TestClient(app) as c:
        yield c


class TestAgentHealth:
    def test_health_returns_online(self, agent_client: TestClient):
        resp = agent_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
        assert "hostname" in data
        assert "timestamp" in data
        assert data["agent_version"] == "2.0.0"


class TestAgentInfo:
    def test_info_has_required_fields(self, agent_client: TestClient):
        resp = agent_client.get("/info")
        assert resp.status_code == 200
        data = resp.json()
        required = ["hostname", "ip", "os", "architecture", "processor", "uptime_seconds"]
        for field in required:
            assert field in data, f"Falta el campo: {field}"

    def test_uptime_is_positive(self, agent_client: TestClient):
        resp = agent_client.get("/info")
        assert resp.json()["uptime_seconds"] > 0


class TestAgentMetrics:
    def test_metrics_structure(self, agent_client: TestClient):
        resp = agent_client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data
        assert "processes" in data

    def test_cpu_percent_valid_range(self, agent_client: TestClient):
        resp = agent_client.get("/metrics")
        cpu = resp.json()["cpu"]["percent"]
        assert 0.0 <= cpu <= 100.0

    def test_ram_percent_valid_range(self, agent_client: TestClient):
        resp = agent_client.get("/metrics")
        ram = resp.json()["memory"]["percent"]
        assert 0.0 <= ram <= 100.0


class TestAgentExecute:
    def test_execute_allowed_command(self, agent_client: TestClient):
        resp = agent_client.post("/execute", json={"command": "whoami"})
        assert resp.status_code == 200
        data = resp.json()
        assert "stdout" in data or "error" in data

    def test_execute_blocked_command(self, agent_client: TestClient):
        resp = agent_client.post("/execute", json={"command": "rm -rf /"})
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert "no permitido" in data["error"].lower()

    def test_execute_empty_command(self, agent_client: TestClient):
        resp = agent_client.post("/execute", json={"command": ""})
        assert resp.status_code == 200
        assert "error" in resp.json()
