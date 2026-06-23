"""
config.py — Configuración centralizada del Servidor Central
Usa pydantic-settings para leer desde .env con validación automática.
Un solo import de `settings` da acceso a toda la configuración tipada.
"""

import secrets
import sys
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    """
    Configuración global del servidor.
    Los valores se leen desde el archivo .env (o variables de entorno del sistema).
    Si una variable requerida falta, el servidor falla al arrancar con un mensaje claro.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Servidor ──────────────────────────────────────────
    server_host: str = Field(default="0.0.0.0", description="Host del servidor FastAPI")
    server_port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:4173")
    environment: str = Field(default="development")

    # ── Agente ────────────────────────────────────────────
    agent_port: int = Field(default=8001, ge=1, le=65535)

    # ── Seguridad ─────────────────────────────────────────
    secret_key: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        description="Clave secreta para firma de tokens. Generada automáticamente si no se define.",
    )

    # ── Base de datos ─────────────────────────────────────
    database_path: str = Field(default="./monitor.db")

    # ── Heartbeat ─────────────────────────────────────────
    heartbeat_interval: int = Field(default=15, ge=5, le=300, description="Segundos entre verificaciones")
    agent_timeout: int = Field(default=5, ge=1, le=30)

    # ── Notificaciones ────────────────────────────────────
    desktop_notifications: bool = Field(default=True)

    # ── Logs ──────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_file: str | None = Field(default=None)

    # ── Active Directory (futuro) ─────────────────────────
    ad_domain: str | None = Field(default=None)
    ad_server: str | None = Field(default=None)
    ad_base_dn: str | None = Field(default=None)
    ad_admin_group: str | None = Field(default=None)

    # ── Propiedades derivadas ─────────────────────────────
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        # Resolver ruta relativa al directorio del servidor
        path = Path(self.database_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        return f"sqlite:///{path.resolve()}"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid:
            msg = f"log_level debe ser uno de: {valid}"
            raise ValueError(msg)
        return v.upper()


# ── Instancia singleton ────────────────────────────────────────────────────────
# Importar así en cualquier módulo: from config import settings
settings = Settings()
