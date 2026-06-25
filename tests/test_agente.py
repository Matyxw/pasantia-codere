"""
test_agente.py — Tests para las funciones internas del Agente Push
"""

import os
import sys
from unittest.mock import MagicMock, mock_open, patch

# Agregar el directorio del agente al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agente"))

import pytest
import agente


def test_get_local_ip():
    """Verifica que se obtenga una IP local válida."""
    ip = agente._get_local_ip()
    assert isinstance(ip, str)
    assert len(ip.split(".")) == 4 or ip == "127.0.0.1" or ip == "::1"


def test_get_metrics():
    """Verifica que la estructura de métricas generadas por el agente sea la esperada."""
    metrics = agente.get_metrics()
    assert isinstance(metrics, dict)
    assert "timestamp" in metrics
    assert "cpu" in metrics
    assert "memory" in metrics
    assert "disk" in metrics
    assert "network" in metrics
    assert "processes" in metrics

    # Detalles de CPU y memoria
    assert "percent" in metrics["cpu"]
    assert 0.0 <= metrics["cpu"]["percent"] <= 100.0
    assert "percent" in metrics["memory"]
    assert 0.0 <= metrics["memory"]["percent"] <= 100.0


def test_execute_allowed_command():
    """Verifica que se ejecuten correctamente los comandos de la whitelist."""
    # hostname está permitido en la whitelist de comandos del agente
    res = agente.execute_command("hostname")
    assert "error" not in res
    assert res["command"] == "hostname"
    assert "exit_code" in res
    assert "stdout" in res


def test_execute_blocked_command():
    """Verifica que se bloqueen los comandos fuera de la whitelist."""
    res = agente.execute_command("rm -rf /")
    assert "error" in res
    assert "no permitido" in res["error"].lower()


def test_discover_server_from_config():
    """Verifica que la IP del servidor se cargue correctamente desde el archivo de configuración."""
    config_data = '{"server_ip": "127.0.0.1"}'
    with patch("builtins.open", mock_open(read_data=config_data)), \
         patch("os.path.exists", return_value=True):
        ip = agente.discover_server()
        assert ip == "127.0.0.1"


def test_agent_main_loop():
    """Verifica la ejecución del bucle principal del agente."""
    def sleep_side_effect(secs):
        if secs == 5:
            raise KeyboardInterrupt
        return

    with patch("agente.discover_server", return_value="127.0.0.1"), \
         patch("agente.requests.post") as mock_post, \
         patch("agente.time.sleep", side_effect=sleep_side_effect):
        
        # Simular respuesta del servidor con un comando pendiente
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pending_commands": [
                {"id": "cmd-123", "command": "hostname"}
            ]
        }
        mock_post.return_value = mock_response

        # Ejecutar el main loop (debe interrumpirse al llamar a sleep)
        with pytest.raises(KeyboardInterrupt):
            agente.main()

        # Verificar que se enviaron las métricas y el resultado del comando
        assert mock_post.call_count >= 2


def test_get_local_ip_fallback():
    """Verifica el fallback de _get_local_ip cuando falla la conexión de socket."""
    with patch("socket.socket") as mock_sock:
        # Hacer que connect() lance un error para forzar el fallback a socket.gethostbyname
        mock_sock.return_value.connect.side_effect = Exception("Connection failed")
        ip = agente._get_local_ip()
        assert isinstance(ip, str)
        assert len(ip) > 0


def test_execute_command_error():
    """Verifica que execute_command maneje correctamente errores al ejecutar subprocess.run."""
    with patch("subprocess.run", side_effect=Exception("Subprocess error")):
        res = agente.execute_command("hostname")
        assert "error" in res
        assert "Subprocess error" in res["error"]
        assert res["command"] == "hostname"




