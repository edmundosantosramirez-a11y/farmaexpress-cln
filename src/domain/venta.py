from datetime import datetime
from typing import List, Optional
from src.domain.value_objects import RecetaMedica
from src.domain.exceptions import DatosDeRecetaIncompletosError, VentaYaCerradaError

class LineaVenta:
    def __init__(self, id_producto: str, id_lote: str, cantidad: int, precio_unitario: float, requiere_receta: bool = False):
        self.id_producto = id_producto
        self.id_lote = id_lote
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario
        self.requiere_receta = requiere_receta

    @property
    def subtotal(self) -> float:
        return round(self.cantidad * self.precio_unitario, 2)

class Venta:
    def __init__(self, id_venta: str, id_sucursal: str, id_cajero: str):
        self.id_venta = id_venta
        self.id_sucursal = id_sucursal
        self.id_cajero = id_cajero
        self.lineas: List[LineaVenta] = []
        self.receta: Optional[RecetaMedica] = None
        self.completada: bool = False
        self.fecha_cierre: Optional[datetime] = None

    def agregar_linea(self, id_producto: str, id_lote: str, cantidad: int, precio_unitario: float, requiere_receta: bool = False):
        if self.completada:
            raise VentaYaCerradaError()
        self.lineas.append(LineaVenta(id_producto, id_lote, cantidad, precio_unitario, requiere_receta))

    def registrar_receta(self, receta: RecetaMedica):
        if self.completada:
            raise VentaYaCerradaError()
        self.receta = receta

    def total(self) -> float:
        return sum(l.subtotal for l in self.lineas)

    def completar_venta(self, fecha_hora: datetime):
        if self.completada:
            raise VentaYaCerradaError()
        if not self.lineas:
            raise ValueError("No se puede completar una venta sin productos.")
        if any(l.requiere_receta for l in self.lineas) and self.receta is None:
            raise DatosDeRecetaIncompletosError("Medicamentos controlados requieren receta.")
        self.completada = True
        self.fecha_cierre = fecha_hora
