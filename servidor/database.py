"""
database.py — SQLite + SQLAlchemy
Tablas: pcs, events, metrics
WAL mode habilitado para acceso concurrente
"""

import os
import sys
from datetime import datetime

from sqlalchemy import Column, Float, Integer, String, Text, create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)


# Habilitar WAL mode y optimizaciones al crear la conexion
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PC(Base):
    __tablename__ = "pcs"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hostname = Column(String)
    os = Column(String)
    registered_at = Column(String, default=lambda: datetime.now().isoformat())
    status = Column(String, default="unknown")  # online | offline | unknown
    last_seen = Column(String)
    last_offline = Column(String)
    last_metrics = Column(Text)  # JSON snapshot de last /metrics


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    pc_id = Column(Integer, index=True)
    pc_name = Column(String)
    pc_ip = Column(String)
    type = Column(String)  # online | offline
    timestamp = Column(String, default=lambda: datetime.now().isoformat(), index=True)
    downtime_seconds = Column(Float)  # Solo para eventos "online": cuanto tiempo estuvo offline


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    pc_id = Column(Integer, index=True)
    timestamp = Column(String, index=True)
    cpu_percent = Column(Float)
    ram_percent = Column(Float)
    ram_used_gb = Column(Float)
    ram_total_gb = Column(Float)
    disk_percent = Column(Float)
    processes_count = Column(Integer)
    network_connections = Column(Integer)
    uptime_seconds = Column(Float)


# Crear tablas si no existen
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
