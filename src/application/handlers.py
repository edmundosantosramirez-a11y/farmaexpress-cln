from datetime import date, datetime
from typing import Optional
from src.application.interfaces import IUnitOfWork
from src.domain.venta import Venta
from src.domain.value_objects import RecetaMedica
from src.domain.fefo import EstrategiaFEFO
from src.domain.exceptions import ReglaDeNegocioExcepcion, StockInsuficienteError

class IniciarVentaHandler:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def ejecutar(self, id_venta: str, id_sucursal: str, id_cajero: str) -> str:
        venta = Venta(id_venta, id_sucursal, id_cajero)
        self.uow.ventas.guardar(venta)
        self.uow.commit()
        return venta.id_venta

class AgregarProductoHandler:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def ejecutar(self, id_venta: str, id_producto: str, cantidad: int, precio: float, requiere_receta: bool, fecha_actual: date):
        venta = self.uow.ventas.obtener_por_id(id_venta)
        if not venta:
            raise ReglaDeNegocioExcepcion("Venta no encontrada.")

        lotes = self.uow.lotes.obtener_por_producto_y_sucursal(id_producto, venta.id_sucursal)
        lote_fefo = EstrategiaFEFO.seleccionar_lote(lotes, cantidad, fecha_actual)

        venta.agregar_linea(id_producto, lote_fefo.id_lote, cantidad, precio, requiere_receta)
        self.uow.ventas.guardar(venta)
        self.uow.commit()
        return lote_fefo.id_lote

class RegistrarRecetaHandler:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def ejecutar(self, id_venta: str, folio: str, cedula: str, medico: str):
        venta = self.uow.ventas.obtener_por_id(id_venta)
        if not venta:
            raise ReglaDeNegocioExcepcion("Venta no encontrada.")
        receta = RecetaMedica(folio, cedula, medico)
        venta.registrar_receta(receta)
        self.uow.ventas.guardar(venta)
        self.uow.commit()

class CompletarVentaHandler:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def ejecutar(self, id_venta: str, fecha_hora: datetime):
        venta = self.uow.ventas.obtener_por_id(id_venta)
        if not venta:
            raise ReglaDeNegocioExcepcion("Venta no encontrada.")

        # Descontar stock de los lotes asignados (RN-07)
        for linea in venta.lineas:
            lote = self.uow.lotes.obtener_por_id(linea.id_lote)
            if not lote:
                raise StockInsuficienteError(f"El lote {linea.id_lote} ya no existe.")
            lote.descontar(linea.cantidad, fecha_hora.date())
            self.uow.lotes.guardar(lote)

        venta.completar_venta(fecha_hora)
        self.uow.ventas.guardar(venta)
        self.uow.commit()
        return venta.total()

class RetirarLoteHandler:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def ejecutar(self, id_lote: str, motivo: str):
        lote = self.uow.lotes.obtener_por_id(id_lote)
        if not lote:
            raise ReglaDeNegocioExcepcion("Lote no encontrado.")
        lote.retirar(motivo)
        self.uow.lotes.guardar(lote)
        self.uow.commit()

class PonerLoteEnCuarentenaHandler:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def ejecutar(self, id_lote: str):
        lote = self.uow.lotes.obtener_por_id(id_lote)
        if not lote:
            raise ReglaDeNegocioExcepcion("Lote no encontrado.")
        lote.poner_en_cuarentena()
        self.uow.lotes.guardar(lote)
        self.uow.commit()

class LiberarCuarentenaHandler:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def ejecutar(self, id_lote: str):
        lote = self.uow.lotes.obtener_por_id(id_lote)
        if not lote:
            raise ReglaDeNegocioExcepcion("Lote no encontrado.")
        lote.liberar_cuarentena()
        self.uow.lotes.guardar(lote)
        self.uow.commit()
