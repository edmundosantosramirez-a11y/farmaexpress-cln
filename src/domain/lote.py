from datetime import date
from src.domain.value_objects import EstadoLote
from src.domain.exceptions import (
    ProductoCaducadoError, LoteRetiradoError, StockInsuficienteError, LoteEnCuarentenaError,
)
from src.domain.specifications import (
    LoteVendible, LoteNoRetirado, LoteNoEnCuarentena, LoteNoCaducado, LoteConExistencia,
)
from src.domain.state_machine import MAQUINA_LOTE


class Lote:
    def __init__(self, id_lote: str, id_producto: str, fecha_caducidad: date, stock: int, estado: EstadoLote = EstadoLote.VIGENTE):
        self.id_lote = id_lote
        self.id_producto = id_producto
        self.fecha_caducidad = fecha_caducidad
        self.stock = stock
        self.estado = estado

    def es_vendible(self, fecha_actual: date) -> bool:
        return LoteVendible(fecha_actual).is_satisfied_by(self)

    def validar_dispensacion(self, cantidad: int, fecha_actual: date):
        if not LoteNoRetirado().is_satisfied_by(self):
            raise LoteRetiradoError(f"Lote {self.id_lote} retirado.")
        if not LoteNoEnCuarentena().is_satisfied_by(self):
            raise LoteEnCuarentenaError(f"Lote {self.id_lote} en cuarentena.")
        if not LoteNoCaducado(fecha_actual).is_satisfied_by(self):
            raise ProductoCaducadoError(f"Lote {self.id_lote} caducado.")
        if not LoteConExistencia(cantidad).is_satisfied_by(self):
            raise StockInsuficienteError(f"Stock insuficiente en lote {self.id_lote}.")

    def descontar(self, cantidad: int, fecha_actual: date):
        self.validar_dispensacion(cantidad, fecha_actual)
        self.stock -= cantidad

    # --- State Machine: todo cambio de estado pasa por aquí ---
    def _transicionar(self, destino: EstadoLote):
        MAQUINA_LOTE.validar(self.estado, destino)
        self.estado = destino

    def retirar(self, motivo: str):
        self._transicionar(EstadoLote.RETIRADO)

    def poner_en_cuarentena(self):
        self._transicionar(EstadoLote.CUARENTENA)

    def liberar_cuarentena(self):
        self._transicionar(EstadoLote.VIGENTE)
