from typing import Dict, List, Optional
from src.domain.lote import Lote
from src.domain.venta import Venta
from src.application.interfaces import ILoteRepository, IVentaRepository, IUnitOfWork

class MemoriaLoteRepository(ILoteRepository):
    def __init__(self):
        self._lotes: Dict[str, Lote] = {}

    def agregar(self, lote: Lote):
        self._lotes[lote.id_lote] = lote

    def obtener_por_id(self, id_lote: str) -> Optional[Lote]:
        return self._lotes.get(id_lote)

    def obtener_por_producto_y_sucursal(self, id_producto: str, id_sucursal: str) -> List[Lote]:
        return [l for l in self._lotes.values() if l.id_producto == id_producto]

    def guardar(self, lote: Lote) -> None:
        self._lotes[lote.id_lote] = lote

class MemoriaVentaRepository(IVentaRepository):
    def __init__(self):
        self._ventas: Dict[str, Venta] = {}

    def obtener_por_id(self, id_venta: str) -> Optional[Venta]:
        return self._ventas.get(id_venta)

    def guardar(self, venta: Venta) -> None:
        self._ventas[venta.id_venta] = venta

class MemoriaUnitOfWork(IUnitOfWork):
    def __init__(self, repo_ventas: MemoriaVentaRepository, repo_lotes: MemoriaLoteRepository):
        self.ventas = repo_ventas
        self.lotes = repo_lotes

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass
