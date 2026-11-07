"""Repositorios SQL (SQLAlchemy). Implementan las interfaces de application/interfaces.py."""
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.application.interfaces import (
    ILoteRepository, IProductoRepository, IUnitOfWork, IVentaRepository,
)
from src.domain.lote import Lote
from src.domain.producto import Producto
from src.domain.state_machine import EstadoVenta
from src.domain.value_objects import EstadoLote, RecetaMedica
from src.domain.venta import LineaVenta, Venta
from src.infrastructure.models import (
    LineaVentaModel, LoteModel, ProductoModel, VentaModel,
)


# ---------- mapeo fila <-> dominio ----------

def _lote_a_dominio(row: LoteModel) -> Lote:
    return Lote(row.id_lote, row.id_producto, row.fecha_caducidad, row.stock, EstadoLote[row.estado])


def _venta_a_dominio(row: VentaModel) -> Venta:
    venta = Venta(row.id_venta, row.id_sucursal, row.id_cajero)
    venta.estado = EstadoVenta[row.estado]
    venta.fecha_cierre = row.fecha_cierre
    venta.lineas = [
        LineaVenta(l.id_producto, l.id_lote, l.cantidad, l.precio_unitario, l.requiere_receta)
        for l in row.lineas
    ]
    if row.receta_folio is not None:
        venta.receta = RecetaMedica(
            folio=row.receta_folio,
            cedula_medico=row.receta_cedula_medico,
            nombre_medico=row.receta_nombre_medico,
            fecha_emision=row.receta_fecha_emision,
        )
    return venta


# ---------- repositorios ----------

class SqlLoteRepository(ILoteRepository):
    def __init__(self, session: Session):
        self.session = session
        # Referencias fuertes a las filas leídas. El identity map de SQLAlchemy es débil: si la fila se descarta
        # antes de guardar, `guardar` recargaría la versión más nueva de la BD y el control de concurrencia
        # optimista (columna `version`) nunca vería el conflicto, perdiendo la actualización en silencio.
        self._leidos: Dict[str, LoteModel] = {}

    def _leer(self, row: LoteModel) -> Lote:
        self._leidos[row.id_lote] = row
        return _lote_a_dominio(row)

    def obtener_por_id(self, id_lote: str) -> Optional[Lote]:
        row = self.session.get(LoteModel, id_lote)
        return self._leer(row) if row is not None else None

    def obtener_por_producto_y_sucursal(self, id_producto: str, id_sucursal: str) -> List[Lote]:
        # El dominio actual no modela existencia por sucursal: se filtra solo por producto.
        filas = self.session.scalars(select(LoteModel).where(LoteModel.id_producto == id_producto)).all()
        return [self._leer(f) for f in filas]

    def guardar(self, lote: Lote) -> None:
        row = self._leidos.get(lote.id_lote) or self.session.get(LoteModel, lote.id_lote)
        if row is None:
            row = LoteModel(id_lote=lote.id_lote)
            self.session.add(row)
        row.id_producto = lote.id_producto
        row.fecha_caducidad = lote.fecha_caducidad
        row.stock = lote.stock
        row.estado = lote.estado.name

    def agregar(self, lote: Lote) -> None:
        self.guardar(lote)


class SqlVentaRepository(IVentaRepository):
    def __init__(self, session: Session):
        self.session = session

    def obtener_por_id(self, id_venta: str) -> Optional[Venta]:
        row = self.session.get(VentaModel, id_venta)
        return _venta_a_dominio(row) if row is not None else None

    def guardar(self, venta: Venta) -> None:
        row = self.session.get(VentaModel, venta.id_venta)
        if row is None:
            row = VentaModel(id_venta=venta.id_venta)
            self.session.add(row)
        row.id_sucursal = venta.id_sucursal
        row.id_cajero = venta.id_cajero
        row.estado = venta.estado.name
        row.fecha_cierre = venta.fecha_cierre
        if venta.receta is not None:
            row.receta_folio = venta.receta.folio
            row.receta_cedula_medico = venta.receta.cedula_medico
            row.receta_nombre_medico = venta.receta.nombre_medico
            row.receta_fecha_emision = venta.receta.fecha_emision
        else:
            row.receta_folio = None
            row.receta_cedula_medico = None
            row.receta_nombre_medico = None
            row.receta_fecha_emision = None
        row.lineas = [
            LineaVentaModel(
                id_producto=l.id_producto,
                id_lote=l.id_lote,
                cantidad=l.cantidad,
                precio_unitario=l.precio_unitario,
                requiere_receta=l.requiere_receta,
            )
            for l in venta.lineas
        ]


class SqlProductoRepository(IProductoRepository):
    def __init__(self, session: Session):
        self.session = session

    def obtener_por_id(self, id_producto: str) -> Optional[Producto]:
        row = self.session.get(ProductoModel, id_producto)
        if row is None:
            return None
        return Producto(row.id_producto, row.nombre, row.precio, row.requiere_receta)

    def guardar(self, producto: Producto) -> None:
        row = self.session.get(ProductoModel, producto.id_producto)
        if row is None:
            row = ProductoModel(id_producto=producto.id_producto)
            self.session.add(row)
        row.nombre = producto.nombre
        row.precio = producto.precio
        row.requiere_receta = producto.requiere_receta


class SqlUnitOfWork(IUnitOfWork):
    """Una sesión (= una transacción) por caso de uso. Si algo falla y no hay commit, nada se persiste."""

    def __init__(self, session_factory):
        self.session: Session = session_factory()
        self.ventas = SqlVentaRepository(self.session)
        self.lotes = SqlLoteRepository(self.session)
        self.productos = SqlProductoRepository(self.session)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def close(self) -> None:
        self.session.close()
