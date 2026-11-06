from datetime import date
from fastapi.testclient import TestClient

from src.api.main import app, repo_lotes
from src.domain.lote import Lote

client = TestClient(app)


def _crear_lote(id_lote: str):
    repo_lotes.agregar(Lote(id_lote, "PROD-ESTADOS", date(2099, 1, 1), 5))


def test_cuarentena_y_liberacion_por_api():
    _crear_lote("LOTE-API-1")
    assert client.post("/lotes/LOTE-API-1/cuarentena").status_code == 200
    r = client.get("/lotes/LOTE-API-1")
    assert r.json()["estado"] == "CUARENTENA"
    assert r.json()["vendible"] is False
    assert r.json()["motivo_no_vendible"] == "Lote en cuarentena."
    assert client.post("/lotes/LOTE-API-1/liberar").status_code == 200
    assert client.get("/lotes/LOTE-API-1").json()["vendible"] is True


def test_lote_retirado_no_puede_liberarse():
    _crear_lote("LOTE-API-2")
    assert client.post("/lotes/LOTE-API-2/retirar", json={"motivo": "alerta"}).status_code == 200
    r = client.post("/lotes/LOTE-API-2/liberar")
    assert r.status_code == 422
    assert "transición no permitida" in r.json()["detail"]


def test_lote_inexistente_devuelve_404():
    assert client.get("/lotes/NO-EXISTE").status_code == 404
