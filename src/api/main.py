from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

from src.infrastructure.memory_repositories import MemoriaLoteRepository, MemoriaVentaRepository, MemoriaUnitOfWork
from src.application.handlers import (
    IniciarVentaHandler,
    AgregarProductoHandler,
    RegistrarRecetaHandler,
    CompletarVentaHandler,
    RetirarLoteHandler
)
from src.domain.lote import Lote
from src.domain.exceptions import ReglaDeNegocioExcepcion

app = FastAPI(
    title="FarmaExpress API - Lógica de Negocio",
    description="Sistema de gestión farmacéutica con validación FEFO, recetas médicas y control de lotes.",
    version="1.0.0"
)

# Inicialización de persistencia y UoW
repo_ventas = MemoriaVentaRepository()
repo_lotes = MemoriaLoteRepository()
uow = MemoriaUnitOfWork(repo_ventas, repo_lotes)

# Semilla inicial de lotes para pruebas inmediatas
repo_lotes.agregar(Lote("LOTE-001", "PARACETAMOL-500", date(2027, 6, 1), 50))
repo_lotes.agregar(Lote("LOTE-002", "PARACETAMOL-500", date(2026, 12, 1), 20)) # FEFO debe priorizar este
repo_lotes.agregar(Lote("LOTE-CTRL", "CLONAZEPAM-2MG", date(2027, 10, 1), 15))

# Modelos DTO de entrada
class IniciarVentaDTO(BaseModel):
    id_venta: str
    id_sucursal: str
    id_cajero: str

class AgregarProductoDTO(BaseModel):
    id_producto: str
    cantidad: int
    precio_unitario: float
    requiere_receta: bool = False

class RegistrarRecetaDTO(BaseModel):
    folio: str
    cedula_medico: str
    nombre_medico: str

class RetirarLoteDTO(BaseModel):
    motivo: str

# Endpoints
@app.post("/ventas", status_code=201, summary="CU-01: Iniciar venta")
def iniciar_venta(dto: IniciarVentaDTO):
    handler = IniciarVentaHandler(uow)
    id_creado = handler.ejecutar(dto.id_venta, dto.id_sucursal, dto.id_cajero)
    return {"mensaje": "Venta iniciada", "id_venta": id_creado}

@app.post("/ventas/{id_venta}/productos", summary="CU-01/CU-03: Agregar producto a venta (Asigna FEFO)")
def agregar_producto(id_venta: str, dto: AgregarProductoDTO):
    handler = AgregarProductoHandler(uow)
    try:
        lote_asignado = handler.ejecutar(
            id_venta=id_venta,
            id_producto=dto.id_producto,
            cantidad=dto.cantidad,
            precio=dto.precio_unitario,
            requiere_receta=dto.requiere_receta,
            fecha_actual=date.today()
        )
        return {"mensaje": "Producto agregado", "lote_despachado": lote_asignado}
    except ReglaDeNegocioExcepcion as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/ventas/{id_venta}/receta", summary="CU-02: Registrar datos de receta médica")
def registrar_receta(id_venta: str, dto: RegistrarRecetaDTO):
    handler = RegistrarRecetaHandler(uow)
    try:
        handler.ejecutar(id_venta, dto.folio, dto.cedula_medico, dto.nombre_medico)
        return {"mensaje": "Receta registrada correctamente"}
    except ReglaDeNegocioExcepcion as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/ventas/{id_venta}/completar", summary="CU-01/CU-02: Completar venta y generar ticket inmutable")
def completar_venta(id_venta: str):
    handler = CompletarVentaHandler(uow)
    try:
        total = handler.ejecutar(id_venta, datetime.now())
        return {"mensaje": "Venta completada exitosamente", "total": total}
    except ReglaDeNegocioExcepcion as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/lotes/{id_lote}/retirar", summary="CU-04: Retirar lote por alerta sanitaria")
def retirar_lote(id_lote: str, dto: RetirarLoteDTO):
    handler = RetirarLoteHandler(uow)
    try:
        handler.ejecutar(id_lote, dto.motivo)
        return {"mensaje": f"Lote {id_lote} retirado del mercado"}
    except ReglaDeNegocioExcepcion as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.get("/health", summary="Health Check")
def health():
    return {"status": "ok"}
