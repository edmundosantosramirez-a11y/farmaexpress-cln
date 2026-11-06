from datetime import date, datetime
import pytest
from src.domain.lote import Lote
from src.domain.venta import Venta
from src.domain.value_objects import EstadoLote, RecetaMedica
from src.domain.fefo import EstrategiaFEFO
from src.domain.exceptions import (
    ProductoCaducadoError, 
    LoteRetiradoError, 
    StockInsuficienteError, 
    DatosDeRecetaIncompletosError,
    VentaYaCerradaError
)

HOY = date(2026, 11, 6)

def test_t01_fefo_selecciona_caducidad_mas_proxima():
    lote_a = Lote("LOTE-A", "PROD-01", date(2026, 12, 1), 10)
    lote_b = Lote("LOTE-B", "PROD-01", date(2027, 5, 1), 10)
    seleccionado = EstrategiaFEFO.seleccionar_lote([lote_b, lote_a], 2, HOY)
    assert seleccionado.id_lote == "LOTE-A"

def test_t02_bloqueo_lote_caducado():
    lote_vencido = Lote("LOTE-CAD", "PROD-01", date(2026, 10, 1), 5)
    with pytest.raises(ProductoCaducadoError):
        lote_vencido.descontar(1, HOY)

def test_t03_bloqueo_lote_retirado():
    lote = Lote("LOTE-RET", "PROD-01", date(2027, 1, 1), 10)
    lote.retirar("Alerta sanitaria")
    with pytest.raises(LoteRetiradoError):
        lote.descontar(1, HOY)

def test_t04_stock_insuficiente():
    lote = Lote("LOTE-POCO", "PROD-01", date(2027, 1, 1), 2)
    with pytest.raises(StockInsuficienteError):
        lote.descontar(5, HOY)

def test_t05_exigencia_receta_medica():
    venta = Venta("V-001", "SUC-01", "CAJ-01")
    venta.agregar_linea("MED-CTRL", "LOTE-01", 1, 150.0, requiere_receta=True)
    with pytest.raises(DatosDeRecetaIncompletosError):
        venta.completar_venta(datetime.now())
    receta = RecetaMedica("FOL-9988", "CED-123456", "Dr. Pérez", HOY)
    venta.registrar_receta(receta)
    venta.completar_venta(datetime.now())
    assert venta.completada is True

def test_venta_inmutable_al_cerrar():
    venta = Venta("V-002", "SUC-01", "CAJ-01")
    venta.agregar_linea("MED-01", "LOTE-01", 1, 50.0)
    venta.completar_venta(datetime.now())
    with pytest.raises(VentaYaCerradaError):
        venta.agregar_linea("MED-02", "LOTE-02", 1, 20.0)
