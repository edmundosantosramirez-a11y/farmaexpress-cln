from datetime import date, datetime
import pytest
from src.infrastructure.memory_repositories import MemoriaLoteRepository, MemoriaVentaRepository, MemoriaUnitOfWork
from src.application.handlers import (
    IniciarVentaHandler, 
    AgregarProductoHandler, 
    RegistrarRecetaHandler, 
    CompletarVentaHandler, 
    RetirarLoteHandler
)
from src.domain.lote import Lote
from src.domain.exceptions import LoteRetiradoError, DatosDeRecetaIncompletosError

HOY = date(2026, 11, 6)

def test_flujo_completo_cu01_venta_normal():
    repo_v = MemoriaVentaRepository()
    repo_l = MemoriaLoteRepository()
    uow = MemoriaUnitOfWork(repo_v, repo_l)

    # Lote disponible
    repo_l.agregar(Lote("L-10", "PARACETAMOL", date(2027, 1, 1), 20))

    # Iniciar venta
    iniciar_handler = IniciarVentaHandler(uow)
    iniciar_handler.ejecutar("V-100", "SUC-CENTRO", "CAJ-01")

    # Agregar producto (asigna lote con FEFO)
    agregar_handler = AgregarProductoHandler(uow)
    lote_asignado = agregar_handler.ejecutar("V-100", "PARACETAMOL", 2, 50.0, False, HOY)
    assert lote_asignado == "L-10"

    # Completar venta
    completar_handler = CompletarVentaHandler(uow)
    total = completar_handler.ejecutar("V-100", datetime.now())
    assert total == 100.0

    # Verificar descuento de inventario
    lote_actualizado = repo_l.obtener_por_id("L-10")
    assert lote_actualizado.stock == 18

def test_cu04_retirar_lote_bloquea_venta():
    repo_v = MemoriaVentaRepository()
    repo_l = MemoriaLoteRepository()
    uow = MemoriaUnitOfWork(repo_v, repo_l)

    repo_l.agregar(Lote("L-20", "AMOXICILINA", date(2027, 1, 1), 10))

    # Retirar lote por alerta
    retirar_handler = RetirarLoteHandler(uow)
    retirar_handler.ejecutar("L-20", "Defecto de empaque")

    iniciar_handler = IniciarVentaHandler(uow)
    iniciar_handler.ejecutar("V-101", "SUC-CENTRO", "CAJ-01")

    # Intentar vender el lote retirado debe fallar
    agregar_handler = AgregarProductoHandler(uow)
    with pytest.raises(Exception):
        agregar_handler.ejecutar("V-101", "AMOXICILINA", 1, 80.0, False, HOY)
