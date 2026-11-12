import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from src.application.interfaces import IUnitOfWork
from src.application.handlers import (
    IniciarVentaHandler,
    AgregarProductoHandler,
    RegistrarRecetaHandler,
    CompletarVentaHandler,
    RetirarLoteHandler,
    PonerLoteEnCuarentenaHandler,
    LiberarCuarentenaHandler,
)
from src.domain.lote import Lote
from src.domain.exceptions import ReglaDeNegocioExcepcion
from src.domain.specifications import LoteVendible
from src.infrastructure.database import crear_engine, crear_session_factory, obtener_database_url
from src.infrastructure.memory_repositories import (
    MemoriaLoteRepository, MemoriaVentaRepository, MemoriaUnitOfWork,
)
from src.infrastructure.models import Base
from src.infrastructure.seed import sembrar_datos_demo
from src.infrastructure.sql_repositories import SqlUnitOfWork

# ---------- Configuración (12-Factor): si hay DATABASE_URL se usa PostgreSQL; si no, memoria ----------
DATABASE_URL = obtener_database_url()
USAR_DB = DATABASE_URL is not None
engine = crear_engine(DATABASE_URL) if USAR_DB else None
SessionLocal = crear_session_factory(engine) if USAR_DB else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    if USAR_DB:
        Base.metadata.create_all(engine)
        if os.getenv("SEED_DEMO_DATA", "true").lower() == "true":
            sembrar_datos_demo(SessionLocal)
    yield


app = FastAPI(
    title="FarmaExpress API - Lógica de Negocio",
    description="Sistema de gestión farmacéutica con validación FEFO, recetas médicas y control de lotes.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configurable por variable de entorno (12-Factor). Permite abrir la interfaz desde otro origen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

INTERFAZ_HTML = Path(__file__).parent / "static" / "index.html"

# ---------- Modo memoria (pruebas unitarias y ejecución sin base de datos) ----------
repo_ventas = MemoriaVentaRepository()
repo_lotes = MemoriaLoteRepository()
uow = MemoriaUnitOfWork(repo_ventas, repo_lotes)

_hoy = date.today()
# Fechas relativas a hoy para que la demo y las pruebas no caduquen con el tiempo.
repo_lotes.agregar(Lote("LOTE-001", "PARACETAMOL-500", _hoy + timedelta(days=300), 50))
repo_lotes.agregar(Lote("LOTE-002", "PARACETAMOL-500", _hoy + timedelta(days=25), 20))  # FEFO debe priorizar este
repo_lotes.agregar(Lote("LOTE-CTRL", "CLONAZEPAM-2MG", _hoy + timedelta(days=330), 15))


def get_uow():
    """Una Unit of Work por petición. Con PostgreSQL, si algo falla no hay commit y no se persiste nada."""
    if not USAR_DB:
        yield uow
        return
    sql_uow = SqlUnitOfWork(SessionLocal)
    try:
        yield sql_uow
    except Exception:
        sql_uow.rollback()
        raise
    finally:
        sql_uow.close()


@app.exception_handler(StaleDataError)
async def conflicto_de_concurrencia(request, exc):
    return JSONResponse(
        status_code=409,
        content={"detail": "El lote fue modificado por otra operación al mismo tiempo. Reintenta."},
    )


@app.exception_handler(IntegrityError)
async def conflicto_de_integridad(request, exc):
    return JSONResponse(status_code=409, content={"detail": "Registro duplicado o violación de integridad."})


# ---------- DTOs de entrada ----------
class IniciarVentaDTO(BaseModel):
    id_venta: str
    id_sucursal: str
    id_cajero: str


class AgregarProductoDTO(BaseModel):
    id_producto: str
    cantidad: int
    # Si el producto está en el catálogo, precio y receta salen del catálogo y estos campos se ignoran.
    precio_unitario: Optional[float] = None
    requiere_receta: Optional[bool] = None


class RegistrarRecetaDTO(BaseModel):
    folio: str
    cedula_medico: str
    nombre_medico: str


class RetirarLoteDTO(BaseModel):
    motivo: str


# ---------- Endpoints ----------
@app.post("/ventas", status_code=201, summary="CU-01: Iniciar venta")
def iniciar_venta(dto: IniciarVentaDTO, u: IUnitOfWork = Depends(get_uow)):
    handler = IniciarVentaHandler(u)
    try:
        id_creado = handler.ejecutar(dto.id_venta, dto.id_sucursal, dto.id_cajero)
        return {"mensaje": "Venta iniciada", "id_venta": id_creado}
    except ReglaDeNegocioExcepcion as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/ventas/{id_venta}/productos", summary="CU-01/CU-03: Agregar producto a venta (Asigna FEFO)")
def agregar_producto(id_venta: str, dto: AgregarProductoDTO, u: IUnitOfWork = Depends(get_uow)):
    handler = AgregarProductoHandler(u)
    try:
        lote_asignado = handler.ejecutar(
            id_venta=id_venta,
            id_producto=dto.id_producto,
            cantidad=dto.cantidad,
            precio=dto.precio_unitario,
            requiere_receta=dto.requiere_receta,
            fecha_actual=date.today(),
        )
        return {"mensaje": "Producto agregado", "lote_despachado": lote_asignado}
    except ReglaDeNegocioExcepcion as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/ventas/{id_venta}/receta", summary="CU-02: Registrar datos de receta médica")
def registrar_receta(id_venta: str, dto: RegistrarRecetaDTO, u: IUnitOfWork = Depends(get_uow)):
    handler = RegistrarRecetaHandler(u)
    try:
        handler.ejecutar(id_venta, dto.folio, dto.cedula_medico, dto.nombre_medico)
        return {"mensaje": "Receta registrada correctamente"}
    except ReglaDeNegocioExcepcion as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/ventas/{id_venta}/completar", summary="CU-01/CU-02: Completar venta y generar ticket inmutable")
def completar_venta(id_venta: str, u: IUnitOfWork = Depends(get_uow)):
    handler = CompletarVentaHandler(u)
    try:
        total = handler.ejecutar(id_venta, datetime.now())
        return {"mensaje": "Venta completada exitosamente", "total": total}
    except ReglaDeNegocioExcepcion as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/ventas/{id_venta}", summary="Consultar venta / ticket")
def consultar_venta(id_venta: str, u: IUnitOfWork = Depends(get_uow)):
    venta = u.ventas.obtener_por_id(id_venta)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada.")
    return {
        "id_venta": venta.id_venta,
        "estado": venta.estado.value,
        "total": venta.total(),
        "receta_registrada": venta.receta is not None,
        "lineas": [
            {
                "id_producto": l.id_producto,
                "id_lote": l.id_lote,
                "cantidad": l.cantidad,
                "precio_unitario": l.precio_unitario,
                "requiere_receta": l.requiere_receta,
            }
            for l in venta.lineas
        ],
    }


@app.post("/lotes/{id_lote}/retirar", summary="CU-04: Retirar lote por alerta sanitaria")
def retirar_lote(id_lote: str, dto: RetirarLoteDTO, u: IUnitOfWork = Depends(get_uow)):
    handler = RetirarLoteHandler(u)
    try:
        handler.ejecutar(id_lote, dto.motivo)
        return {"mensaje": f"Lote {id_lote} retirado del mercado"}
    except ReglaDeNegocioExcepcion as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/lotes/{id_lote}/cuarentena", summary="CU-04: Poner lote en cuarentena")
def poner_en_cuarentena(id_lote: str, u: IUnitOfWork = Depends(get_uow)):
    try:
        PonerLoteEnCuarentenaHandler(u).ejecutar(id_lote)
        return {"mensaje": f"Lote {id_lote} en cuarentena"}
    except ReglaDeNegocioExcepcion as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/lotes/{id_lote}/liberar", summary="CU-04: Liberar lote de cuarentena")
def liberar_cuarentena(id_lote: str, u: IUnitOfWork = Depends(get_uow)):
    try:
        LiberarCuarentenaHandler(u).ejecutar(id_lote)
        return {"mensaje": f"Lote {id_lote} liberado"}
    except ReglaDeNegocioExcepcion as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/lotes/{id_lote}", summary="Consultar lote (estado y si es vendible hoy)")
def consultar_lote(id_lote: str, u: IUnitOfWork = Depends(get_uow)):
    lote = u.lotes.obtener_por_id(id_lote)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado.")
    spec = LoteVendible(date.today())
    return {
        "id_lote": lote.id_lote,
        "estado": getattr(lote.estado, "value", lote.estado),
        "stock": lote.stock,
        "fecha_caducidad": lote.fecha_caducidad.isoformat(),
        "vendible": spec.is_satisfied_by(lote),
        "motivo_no_vendible": spec.motivo_rechazo(lote),
    }


@app.get("/health", summary="Health Check")
def health():
    return {"status": "ok"}


@app.get("/info", summary="Información de despliegue (tipo de persistencia activa)")
def info():
    return {"persistencia": "postgresql" if USAR_DB else "memoria"}


# ---------- Interfaz web para el usuario ----------
@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse(url="/app")


@app.get("/app", include_in_schema=False)
def interfaz():
    """Interfaz web amigable (punto de venta e inventario) que consume esta misma API."""
    return FileResponse(INTERFAZ_HTML, media_type="text/html")
    return {"status": "ok"}


@app.get("/info", summary="Información de despliegue (tipo de persistencia activa)")
def info():
    return {"persistencia": "postgresql" if USAR_DB else "memoria"}
