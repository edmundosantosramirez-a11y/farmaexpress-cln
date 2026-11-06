from datetime import date, datetime
import pytest

from src.domain.lote import Lote
from src.domain.venta import Venta
from src.domain.value_objects import EstadoLote
from src.domain.state_machine import MAQUINA_LOTE, MAQUINA_VENTA, EstadoVenta
from src.domain.exceptions import TransicionInvalidaError, VentaYaCerradaError


def nuevo_lote():
    return Lote("L1", "P1", date(2027, 6, 1), 10)


def test_vigente_a_cuarentena_y_liberar():
    l = nuevo_lote()
    l.poner_en_cuarentena()
    assert l.estado == EstadoLote.CUARENTENA
    l.liberar_cuarentena()
    assert l.estado == EstadoLote.VIGENTE


def test_vigente_a_retirado():
    l = nuevo_lote()
    l.retirar("alerta sanitaria")
    assert l.estado == EstadoLote.RETIRADO


def test_retirado_es_irreversible():
    l = nuevo_lote()
    l.retirar("alerta")
    with pytest.raises(TransicionInvalidaError):
        l.liberar_cuarentena()
    with pytest.raises(TransicionInvalidaError):
        l.poner_en_cuarentena()
    assert l.estado == EstadoLote.RETIRADO


def test_no_se_libera_un_lote_que_no_esta_en_cuarentena():
    with pytest.raises(TransicionInvalidaError):
        nuevo_lote().liberar_cuarentena()


def test_maquina_lote_destinos():
    assert MAQUINA_LOTE.destinos(EstadoLote.VIGENTE) == {EstadoLote.CUARENTENA, EstadoLote.RETIRADO}
    assert MAQUINA_LOTE.destinos(EstadoLote.RETIRADO) == set()


def test_venta_abierta_a_completada():
    v = Venta("V1", "S1", "C1")
    assert v.estado == EstadoVenta.ABIERTA and not v.completada
    v.agregar_linea("P1", "L1", 1, 10.0)
    v.completar_venta(datetime(2026, 11, 6, 12, 0))
    assert v.estado == EstadoVenta.COMPLETADA and v.completada


def test_venta_completada_es_inmutable():
    v = Venta("V1", "S1", "C1")
    v.agregar_linea("P1", "L1", 1, 10.0)
    v.completar_venta(datetime(2026, 11, 6, 12, 0))
    with pytest.raises(VentaYaCerradaError):
        v.agregar_linea("P1", "L1", 1, 10.0)
    with pytest.raises(VentaYaCerradaError):
        v.completar_venta(datetime(2026, 11, 6, 12, 5))


def test_maquina_venta_no_permite_reabrir():
    assert not MAQUINA_VENTA.puede(EstadoVenta.COMPLETADA, EstadoVenta.ABIERTA)
