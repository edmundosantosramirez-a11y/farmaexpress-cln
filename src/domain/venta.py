from datetime import datetime
from typing import List, Optional
from src.domain.value_objects import RecetaMedica
from src.domain.exceptions import DatosDeRecetaIncompletosError, VentaYaCerradaError
from src.domain.specifications import VentaConProductos, VentaConRecetaCompleta
from src.domain.state_machine import EstadoVenta, MAQUINA_VENTA


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
        self.estado: EstadoVenta = EstadoVenta.ABIERTA
        self.fecha_cierre: Optional[datetime] = None

    @property
    def completada(self) -> bool:
        return self.estado == EstadoVenta.COMPLETADA

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
        if not VentaConProductos().is_satisfied_by(self):
            raise ValueError(VentaConProductos.mensaje)
        if not VentaConRecetaCompleta().is_satisfied_by(self):
            raise DatosDeRecetaIncompletosError(VentaConRecetaCompleta.mensaje)
        MAQUINA_VENTA.validar(self.estado, EstadoVenta.COMPLETADA)
        self.estado = EstadoVenta.COMPLETADA
        self.fecha_cierre = fecha_hora
