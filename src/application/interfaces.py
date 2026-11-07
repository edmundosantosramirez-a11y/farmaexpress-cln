from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.lote import Lote
from src.domain.venta import Venta
from src.domain.producto import Producto

class ILoteRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id_lote: str) -> Optional[Lote]:
        pass

    @abstractmethod
    def obtener_por_producto_y_sucursal(self, id_producto: str, id_sucursal: str) -> List[Lote]:
        pass

    @abstractmethod
    def guardar(self, lote: Lote) -> None:
        pass

class IVentaRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id_venta: str) -> Optional[Venta]:
        pass

    @abstractmethod
    def guardar(self, venta: Venta) -> None:
        pass

class IProductoRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id_producto: str) -> Optional[Producto]:
        pass

    @abstractmethod
    def guardar(self, producto: Producto) -> None:
        pass

class IUnitOfWork(ABC):
    ventas: IVentaRepository
    lotes: ILoteRepository
    productos: IProductoRepository

    @abstractmethod
    def commit(self) -> None:
        pass

    @abstractmethod
    def rollback(self) -> None:
        pass
