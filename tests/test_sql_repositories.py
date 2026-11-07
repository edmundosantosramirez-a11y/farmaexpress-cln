"""Pruebas de integración contra una base real.

Usan TEST_DATABASE_URL (PostgreSQL en Docker Compose y en el CI). Si no existe, usan un SQLite temporal.
"""
import os
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.orm.exc import StaleDataError

from src.application.handlers import (
    AgregarProductoHandler, CompletarVentaHandler, IniciarVentaHandler, RegistrarRecetaHandler,
)
from src.domain.exceptions import DatosDeRecetaIncompletosError, StockInsuficienteError
from src.domain.lote import Lote
from src.domain.producto import Producto
from src.domain.state_machine import EstadoVenta
from src.domain.value_objects import EstadoLote
from src.infrastructure.database import crear_engine, crear_session_factory
from src.infrastructure.models import Base
from src.infrastructure.sql_repositories import SqlUnitOfWork

HOY = date.today()


@pytest.fixture
def factory(tmp_path):
    url = os.getenv("TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    engine = crear_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield crear_session_factory(engine)
    Base.metadata.drop_all(engine)
    engine.dispose()


def _sembrar(factory):
    uow = SqlUnitOfWork(factory)
    uow.productos.guardar(Producto("PARA", "Paracetamol", 35.0, False))
    uow.productos.guardar(Producto("CLONA", "Clonazepam", 180.0, True))
    uow.lotes.guardar(Lote("L-LARGO", "PARA", HOY + timedelta(days=300), 50))
    uow.lotes.guardar(Lote("L-CORTO", "PARA", HOY + timedelta(days=25), 20))
    uow.lotes.guardar(Lote("L-CTRL", "CLONA", HOY + timedelta(days=300), 15))
    uow.commit()
    uow.close()


def test_lote_se_guarda_y_se_recupera_con_su_estado(factory):
    uow = SqlUnitOfWork(factory)
    uow.lotes.guardar(Lote("L1", "P1", HOY + timedelta(days=100), 7))
    uow.commit()
    lote = uow.lotes.obtener_por_id("L1")
    lote.retirar("alerta")
    uow.lotes.guardar(lote)
    uow.commit()
    uow.close()

    otra = SqlUnitOfWork(factory)
    leido = otra.lotes.obtener_por_id("L1")
    assert leido.estado == EstadoLote.RETIRADO and leido.stock == 7
    assert otra.lotes.obtener_por_id("NO-EXISTE") is None
    otra.close()


def test_flujo_cu01_fefo_y_descuento_persistido(factory):
    _sembrar(factory)
    uow = SqlUnitOfWork(factory)
    IniciarVentaHandler(uow).ejecutar("V1", "S1", "C1")
    lote = AgregarProductoHandler(uow).ejecutar("V1", "PARA", 2, fecha_actual=HOY)
    assert lote == "L-CORTO"  # FEFO: caduca antes
    total = CompletarVentaHandler(uow).ejecutar("V1", datetime.now())
    assert total == 70.0  # precio del catálogo
    uow.close()

    verificacion = SqlUnitOfWork(factory)
    assert verificacion.lotes.obtener_por_id("L-CORTO").stock == 18
    venta = verificacion.ventas.obtener_por_id("V1")
    assert venta.estado == EstadoVenta.COMPLETADA and venta.fecha_cierre is not None
    assert venta.lineas[0].id_lote == "L-CORTO"
    verificacion.close()


def test_receta_obligatoria_viene_del_catalogo_y_se_persiste(factory):
    _sembrar(factory)
    uow = SqlUnitOfWork(factory)
    IniciarVentaHandler(uow).ejecutar("V2", "S1", "C1")
    # El cajero dice que NO requiere receta, pero el catálogo manda.
    AgregarProductoHandler(uow).ejecutar("V2", "CLONA", 1, precio=1.0, requiere_receta=False, fecha_actual=HOY)
    with pytest.raises(DatosDeRecetaIncompletosError):
        CompletarVentaHandler(uow).ejecutar("V2", datetime.now())
    uow.rollback()
    RegistrarRecetaHandler(uow).ejecutar("V2", "F-001", "1234567", "Dr. Prueba")
    assert CompletarVentaHandler(uow).ejecutar("V2", datetime.now()) == 180.0
    uow.close()

    verificacion = SqlUnitOfWork(factory)
    venta = verificacion.ventas.obtener_por_id("V2")
    assert venta.receta.folio == "F-001" and venta.receta.cedula_medico == "1234567"
    verificacion.close()


def test_rollback_no_deja_descuentos_a_medias(factory):
    """T-06 de U3: si falla al completar la venta, no hay ticket ni descuento de existencia."""
    uow = SqlUnitOfWork(factory)
    uow.productos.guardar(Producto("P", "Producto", 10.0, False))
    uow.lotes.guardar(Lote("L-A", "P", HOY + timedelta(days=100), 5))
    uow.commit()
    IniciarVentaHandler(uow).ejecutar("V3", "S1", "C1")
    # Dos líneas del mismo lote: cada una cabe sola (3 <= 5), juntas no (6 > 5).
    AgregarProductoHandler(uow).ejecutar("V3", "P", 3, fecha_actual=HOY)
    AgregarProductoHandler(uow).ejecutar("V3", "P", 3, fecha_actual=HOY)
    with pytest.raises(StockInsuficienteError):
        CompletarVentaHandler(uow).ejecutar("V3", datetime.now())
    uow.rollback()
    uow.close()

    verificacion = SqlUnitOfWork(factory)
    assert verificacion.lotes.obtener_por_id("L-A").stock == 5
    assert verificacion.ventas.obtener_por_id("V3").estado == EstadoVenta.ABIERTA
    verificacion.close()


def test_concurrencia_optimista_dos_cajas_mismo_lote(factory):
    uow = SqlUnitOfWork(factory)
    uow.lotes.guardar(Lote("L-C", "P", HOY + timedelta(days=100), 10))
    uow.commit()
    uow.close()

    caja1, caja2 = SqlUnitOfWork(factory), SqlUnitOfWork(factory)
    try:
        l1 = caja1.lotes.obtener_por_id("L-C")
        l2 = caja2.lotes.obtener_por_id("L-C")  # ambas cajas leen stock 10
        l1.descontar(1, HOY)
        caja1.lotes.guardar(l1)
        caja1.commit()
        l2.descontar(1, HOY)
        caja2.lotes.guardar(l2)
        with pytest.raises(StaleDataError):
            caja2.commit()  # la segunda caja trabajaba con datos viejos: se rechaza
        caja2.rollback()
    finally:
        caja1.close()
        caja2.close()

    verificacion = SqlUnitOfWork(factory)
    assert verificacion.lotes.obtener_por_id("L-C").stock == 9  # no se perdió ni se duplicó el descuento
    verificacion.close()
