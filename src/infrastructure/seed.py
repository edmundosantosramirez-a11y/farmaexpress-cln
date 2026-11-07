"""Datos de demostración (ilustrativos, no son datos reales de FarmaExpress)."""
from datetime import date, timedelta

from sqlalchemy import select

from src.infrastructure.models import LoteModel, ProductoModel

# (id_producto, nombre, precio, requiere_receta)
PRODUCTOS_DEMO = [
    ("PARACETAMOL-500", "Paracetamol 500 mg", 35.0, False),
    ("CLONAZEPAM-2MG", "Clonazepam 2 mg", 180.0, True),
]


def sembrar_datos_demo(session_factory, hoy: date = None) -> bool:
    """Inserta catálogo y lotes solo si no hay lotes. Fechas relativas a hoy para que la demo no caduque."""
    hoy = hoy or date.today()
    with session_factory() as session:
        if session.scalars(select(LoteModel).limit(1)).first() is not None:
            return False
        for id_producto, nombre, precio, requiere in PRODUCTOS_DEMO:
            session.add(ProductoModel(id_producto=id_producto, nombre=nombre, precio=precio, requiere_receta=requiere))
        # LOTE-002 caduca antes que LOTE-001: FEFO debe despachar primero LOTE-002.
        session.add(LoteModel(id_lote="LOTE-001", id_producto="PARACETAMOL-500",
                              fecha_caducidad=hoy + timedelta(days=300), stock=50, estado="VIGENTE"))
        session.add(LoteModel(id_lote="LOTE-002", id_producto="PARACETAMOL-500",
                              fecha_caducidad=hoy + timedelta(days=25), stock=20, estado="VIGENTE"))
        session.add(LoteModel(id_lote="LOTE-CTRL", id_producto="CLONAZEPAM-2MG",
                              fecha_caducidad=hoy + timedelta(days=330), stock=15, estado="VIGENTE"))
        session.commit()
        return True
