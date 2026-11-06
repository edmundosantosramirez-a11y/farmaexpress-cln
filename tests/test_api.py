from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_flujo_completo_api_venta():
    # 1. Iniciar venta
    res = client.post("/ventas", json={
        "id_venta": "V-API-01",
        "id_sucursal": "SUC-01",
        "id_cajero": "CAJ-01"
    })
    assert res.status_code == 201

    # 2. Agregar medicamento común (debe asignar LOTE-002 por FEFO al vencer antes)
    res = client.post("/ventas/V-API-01/productos", json={
        "id_producto": "PARACETAMOL-500",
        "cantidad": 2,
        "precio_unitario": 45.0,
        "requiere_receta": False
    })
    assert res.status_code == 200
    assert res.json()["lote_despachado"] == "LOTE-002"

    # 3. Completar venta
    res = client.post("/ventas/V-API-01/completar")
    assert res.status_code == 200
    assert res.json()["total"] == 90.0
