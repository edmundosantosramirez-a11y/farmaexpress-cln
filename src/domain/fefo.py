from datetime import date
from typing import List
from src.domain.lote import Lote
from src.domain.exceptions import StockInsuficienteError

class EstrategiaFEFO:
    @staticmethod
    def seleccionar_lote(lotes: List[Lote], cantidad: int, fecha_actual: date) -> Lote:
        candidatos = [l for l in lotes if l.es_vendible(fecha_actual) and l.stock >= cantidad]
        if not candidatos:
            raise StockInsuficienteError("No hay lotes vigentes disponibles con stock suficiente.")
        candidatos.sort(key=lambda x: x.fecha_caducidad)
        return candidatos[0]
