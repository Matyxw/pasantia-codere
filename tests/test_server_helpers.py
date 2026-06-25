"""
test_server_helpers.py — Tests para configuraciones, notificaciones y el planificador (scheduler)
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Agregar servidor al PATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servidor"))

import pytest

import config
import notificaciones
import scheduler


def test_config_defaults():
    """Verifica que las configuraciones por defecto de settings estén correctas."""
    assert config.settings.server_host == "0.0.0.0"
    assert config.settings.server_port == 8000
    assert config.settings.agent_port == 8001
    assert isinstance(config.settings.cors_origins_list, list)
    assert not config.settings.is_production


def test_notificaciones_format_downtime():
    """Verifica el formato del tiempo de inactividad."""
    assert notificaciones._format_downtime(None) == ""
    assert notificaciones._format_downtime(45) == "45s"
    assert notificaciones._format_downtime(130) == "2m 10s"


def test_notificaciones_calls():
    """Verifica que las notificaciones no lancen excepciones al ejecutarse."""
    try:
        notificaciones.notify_offline("Test-PC", "192.168.1.100")
        notificaciones.notify_online("Test-PC", "192.168.1.100", 90.0)
    except Exception as e:
        pytest.fail(f"notify functions raised an exception: {e}")


def test_scheduler_lifecycle():
    """Verifica que se pueda inicializar, arrancar y detener el scheduler correctamente."""
    loop = MagicMock()
    broadcast_cb = MagicMock()

    try:
        scheduler.init(loop, broadcast_cb)
        scheduler.start()
        scheduler.stop()
    except Exception as e:
        pytest.fail(f"Scheduler lifecycle failed: {e}")


def test_scheduler_heartbeat_pc_goes_offline():
    """Verifica que el scheduler marque una PC offline si no reporta métricas a tiempo."""
    from datetime import datetime, timedelta

    from conftest import TestSessionLocal
    from database import PC, Event

    # Configurar PC con last_seen de hace 30 segundos
    last_seen_time = (datetime.now() - timedelta(seconds=30)).isoformat()
    pc = PC(ip="10.0.0.5", name="PC-Timeout", status="online", last_seen=last_seen_time)

    with patch("scheduler.SessionLocal", TestSessionLocal), \
         patch("scheduler.notify_offline") as mock_notify:

        # Guardar en base de datos de test
        db = TestSessionLocal()
        db.add(pc)
        db.commit()
        db.refresh(pc)
        db.close()

        # Ejecutar la verificación del scheduler
        scheduler._heartbeat()

        # Verificar cambios
        db = TestSessionLocal()
        updated_pc = db.query(PC).filter(PC.id == pc.id).first()
        assert updated_pc.status == "offline"

        # Verificar creación del evento
        event = db.query(Event).filter(Event.pc_id == pc.id).first()
        assert event is not None
        assert event.type == "offline"
        db.close()


def test_config_database_url():
    """Verifica que database_url derive la URL de SQLite correctamente."""
    assert "sqlite:///" in config.settings.database_url


def test_config_invalid_log_level():
    """Verifica que se lance ValidationError al configurar un nivel de log inválido."""
    from pydantic import ValidationError

    from config import Settings

    with pytest.raises(ValidationError):
        Settings(log_level="INVALID_LEVEL")


def test_real_get_db():
    """Verifica el generador get_db real usado en FastAPI."""
    from database import get_db
    generator = get_db()
    db = next(generator)
    assert db is not None
    try:
        next(generator)
    except StopIteration:
        pass


def test_scheduler_check_pc_invalid_last_seen():
    """Verifica que el scheduler maneje correctamente campos last_seen con formatos inválidos."""
    from conftest import TestSessionLocal
    from database import PC

    pc = PC(ip="10.0.0.9", name="PC-Invalid-Date", status="online", last_seen="invalid-date-string")

    with patch("scheduler.SessionLocal", TestSessionLocal), \
         patch("scheduler.notify_offline") as mock_notify:
        db = TestSessionLocal()
        db.add(pc)
        db.commit()
        db.refresh(pc)
        db.close()

        scheduler._heartbeat()

        db = TestSessionLocal()
        updated_pc = db.query(PC).filter(PC.id == pc.id).first()
        assert updated_pc.status == "offline"
        db.close()



