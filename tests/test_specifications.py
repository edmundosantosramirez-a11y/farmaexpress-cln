from datetime import date, datetime
import pytest

from src.domain.lote import Lote
from src.domain.venta import Venta
from src.domain.value_objects import EstadoLote, RecetaMedica
from src.domain.specifications import (
    LoteVendible, LoteNoCaducado, LoteNoRetirado, LoteProximoACaducar,
    ExistenciaBajoMinimo, VentaConRecetaCompleta,
)
from src.domain.exceptions import LoteEnCuarentenaError

HOY = date(2026, 11, 6)


def lote(caduca=date(2027, 6, 1), stock=10, estado=EstadoLote.VIGENTE):
    return Lote("L1", "P1", caduca, stock, estado)


def test_lote_vigente_con_stock_es_vendible():
    assert LoteVendible(HOY).is_satisfied_by(lote())


def test_lote_caducado_no_es_vendible_y_da_motivo():
    spec = LoteVendible(HOY)
    l = lote(caduca=date(2026, 11, 6))  # vence hoy: ya no se vende (RN-02)
    assert not spec.is_satisfied_by(l)
    assert spec.motivo_rechazo(l) == "Lote caducado."


def test_lote_retirado_tiene_prioridad_en_el_motivo():
    spec = LoteVendible(HOY)
    l = lote(caduca=date(2020, 1, 1), estado=EstadoLote.RETIRADO)
    assert spec.motivo_rechazo(l) == "Lote retirado."


def test_lote_en_cuarentena_no_es_vendible():
    assert not LoteVendible(HOY).is_satisfied_by(lote(estado=EstadoLote.CUARENTENA))


def test_lote_sin_stock_o_insuficiente():
    assert not LoteVendible(HOY).is_satisfied_by(lote(stock=0))
    assert not LoteVendible(HOY, cantidad=11).is_satisfied_by(lote(stock=10))


def test_composicion_and_or_not():
    l = lote(estado=EstadoLote.RETIRADO)
    assert (~LoteNoRetirado()).is_satisfied_by(l)
    assert (LoteNoRetirado() | LoteNoCaducado(HOY)).is_satisfied_by(l)
    assert not (LoteNoRetirado() & LoteNoCaducado(HOY)).is_satisfied_by(l)


@pytest.mark.parametrize("dias_restantes,dias_umbral,esperado", [
    (89, 90, True), (90, 90, True), (91, 90, False), (30, 30, True), (0, 30, False),
])
def test_lote_proximo_a_caducar_umbrales(dias_restantes, dias_umbral, esperado):
    from datetime import timedelta
    l = lote(caduca=HOY + timedelta(days=dias_restantes))
    assert LoteProximoACaducar(HOY, dias_umbral).is_satisfied_by(l) is esperado


def test_existencia_bajo_minimo():
    assert ExistenciaBajoMinimo(10).is_satisfied_by(9)
    assert not ExistenciaBajoMinimo(10).is_satisfied_by(10)


def test_venta_con_receta_completa():
    v = Venta("V1", "S1", "C1")
    v.agregar_linea("CLONAZEPAM", "L1", 1, 100.0, requiere_receta=True)
    assert not VentaConRecetaCompleta().is_satisfied_by(v)
    v.registrar_receta(RecetaMedica("F1", "1234567", "Dr. X"))
    assert VentaConRecetaCompleta().is_satisfied_by(v)


def test_venta_sin_receta_obligatoria_es_valida():
    v = Venta("V1", "S1", "C1")
    v.agregar_linea("PARACETAMOL", "L1", 1, 20.0)
    assert VentaConRecetaCompleta().is_satisfied_by(v)


def test_descontar_de_lote_en_cuarentena_se_rechaza():
    l = lote(estado=EstadoLote.CUARENTENA)
    with pytest.raises(LoteEnCuarentenaError):
        l.descontar(1, HOY)
