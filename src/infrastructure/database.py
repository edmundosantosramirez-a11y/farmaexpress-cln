"""Configuración de la base de datos (12-Factor: todo viene de variables de entorno)."""
import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


def obtener_database_url() -> Optional[str]:
    """DATABASE_URL del entorno. Render/Heroku a veces entregan 'postgres://'; SQLAlchemy pide 'postgresql://'."""
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def crear_engine(url: str) -> Engine:
    opciones = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        opciones["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **opciones)


def crear_session_factory(engine: Engine):
    return sessionmaker(bind=engine, expire_on_commit=False)
