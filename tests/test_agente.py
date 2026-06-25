"""
test_agente.py — Tests para las funciones internas del Agente Push
"""

import os
import sys
from unittest.mock import MagicMock, mock_open, patch

# Agregar el directorio del agente al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agente"))

from agente import _get_local_ip, execute_command, get_metrics


class TestAgentFunctions:
    def test_get_local_ip(self):
        ip = _get_local_ip()
        assert isinstance(ip, str)
        assert len(ip.split(".")) == 4 or ":" in ip

    def test_get_metrics(self):
        metrics = get_metrics()
        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
        assert "network" in metrics
        assert "processes" in metrics

        # Verificar rangos válidos
        assert 0.0 <= metrics["cpu"]["percent"] <= 100.0
        assert 0.0 <= metrics["memory"]["percent"] <= 100.0


class TestAgentExecute:
    def test_execute_allowed_command(self):
        res = execute_command("whoami")
        assert "error" not in res or res["error"] == ""
        assert res["exit_code"] == 0 or res["exit_code"] == 1
        assert "stdout" in res
        assert res["command"] == "whoami"

    def test_execute_blocked_command(self):
        res = execute_command("rm -rf /")
        assert "error" in res
        assert "no permitido" in res["error"].lower()

    def test_execute_empty_command(self):
        res = execute_command("")
        assert "error" in res
        assert "no permitido" in res["error"].lower()
