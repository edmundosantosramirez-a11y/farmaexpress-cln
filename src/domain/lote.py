from datetime import date
from src.domain.value_objects import EstadoLote
from src.domain.exceptions import ProductoCaducadoError, LoteRetiradoError, StockInsuficienteError

class Lote:
    def __init__(self, id_lote: str, id_producto: str, fecha_caducidad: date, stock: int, estado: EstadoLote = EstadoLote.VIGENTE):
        self.id_lote = id_lote
        self.id_producto = id_producto
        self.fecha_caducidad = fecha_caducidad
        self.stock = stock
        self.estado = estado

    def es_vendible(self, fecha_actual: date) -> bool:
        if self.estado in (EstadoLote.RETIRADO, EstadoLote.CUARENTENA):
            return False
        if self.fecha_caducidad <= fecha_actual:
            return False
        return self.stock > 0

    def validar_dispensacion(self, cantidad: int, fecha_actual: date):
        if self.estado == EstadoLote.RETIRADO:
            raise LoteRetiradoError(f"Lote {self.id_lote} retirado.")
        if self.fecha_caducidad <= fecha_actual:
            raise ProductoCaducadoError(f"Lote {self.id_lote} caducado.")
        if self.stock < cantidad:
            raise StockInsuficienteError(f"Stock insuficiente en lote {self.id_lote}.")

    def descontar(self, cantidad: int, fecha_actual: date):
        self.validar_dispensacion(cantidad, fecha_actual)
        self.stock -= cantidad

    def retirar(self, motivo: str):
        self.estado = EstadoLote.RETIRADO

    def poner_en_cuarentena(self):
        if self.estado != EstadoLote.RETIRADO:
            self.estado = EstadoLote.CUARENTENA
