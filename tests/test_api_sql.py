"""La API completa contra la base de datos (sustituye la Unit of Work en memoria por la SQL)."""
import os

import pytest
from fastapi.testclient import TestClient

from src.api import main
from src.infrastructure.database import crear_engine, crear_session_factory
from src.infrastructure.models import Base
from src.infrastructure.seed import PRODUCTOS_DEMO, sembrar_datos_demo
from src.infrastructure.sql_repositories import SqlUnitOfWork

PRECIO_CLONAZEPAM = next(p[2] for p in PRODUCTOS_DEMO if p[0] == "CLONAZEPAM-2MG")


@pytest.fixture
def client(tmp_path):
    url = os.getenv("TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    engine = crear_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = crear_session_factory(engine)
    sembrar_datos_demo(factory)

    def _uow_sql():
        uow = SqlUnitOfWork(factory)
        try:
            yield uow
        except Exception:
            uow.rollback()
            raise
        finally:
            uow.close()

    main.app.dependency_overrides[main.get_uow] = _uow_sql
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_fefo_y_ticket_persistido(client):
    assert client.post("/ventas", json={"id_venta": "VA-1", "id_sucursal": "S1", "id_cajero": "C1"}).status_code == 201
    r = client.post("/ventas/VA-1/productos", json={"id_producto": "PARACETAMOL-500", "cantidad": 2})
    assert r.status_code == 200 and r.json()["lote_despachado"] == "LOTE-002"
    assert client.post("/ventas/VA-1/completar").status_code == 200
    ticket = client.get("/ventas/VA-1").json()
    assert ticket["estado"] == "COMPLETADA" and ticket["lineas"][0]["id_lote"] == "LOTE-002"
    assert client.get("/lotes/LOTE-002").json()["stock"] == 18


def test_el_catalogo_obliga_la_receta_aunque_el_cajero_diga_que_no(client):
    client.post("/ventas", json={"id_venta": "VA-2", "id_sucursal": "S1", "id_cajero": "C1"})
    client.post("/ventas/VA-2/productos",
                json={"id_producto": "CLONAZEPAM-2MG", "cantidad": 1, "precio_unitario": 1.0, "requiere_receta": False})
    r = client.post("/ventas/VA-2/completar")
    assert r.status_code == 422
    assert client.post("/ventas/VA-2/receta",
                       json={"folio": "F-9", "cedula_medico": "1234567", "nombre_medico": "Dr. Prueba"}).status_code == 200
    r = client.post("/ventas/VA-2/completar")
    assert r.status_code == 200 and r.json()["total"] == PRECIO_CLONAZEPAM


def test_lote_retirado_en_bd_ya_no_se_despacha(client):
    assert client.post("/lotes/LOTE-002/retirar", json={"motivo": "alerta"}).status_code == 200
    client.post("/ventas", json={"id_venta": "VA-3", "id_sucursal": "S1", "id_cajero": "C1"})
    r = client.post("/ventas/VA-3/productos", json={"id_producto": "PARACETAMOL-500", "cantidad": 1})
    assert r.json()["lote_despachado"] == "LOTE-001"
    assert client.post("/lotes/LOTE-002/liberar").status_code == 422  # retirado es irreversible


def test_no_se_puede_pisar_una_venta_ya_completada(client):
    body = {"id_venta": "VA-4", "id_sucursal": "S1", "id_cajero": "C1"}
    assert client.post("/ventas", json=body).status_code == 201
    client.post("/ventas/VA-4/productos", json={"id_producto": "PARACETAMOL-500", "cantidad": 1})
    assert client.post("/ventas/VA-4/completar").status_code == 200
    # Reusar el id no debe reabrir ni borrar el ticket inmutable.
    assert client.post("/ventas", json=body).status_code == 422
    assert client.get("/ventas/VA-4").json()["estado"] == "COMPLETADA"
