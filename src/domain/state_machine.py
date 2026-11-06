"""State Machine: estados y transiciones permitidas de Lote y Venta.

Supuestos (a documentar en un ADR, el BRD no los define):
  - Un lote retirado es irreversible (U3, Etapa 5).
  - La cuarentena puede liberarse (vuelve a VIGENTE) o terminar en retiro.
  - Una venta solo pasa de ABIERTA a COMPLETADA; cancelar queda fuera (H04).
"""
from enum import Enum
from typing import Dict, Generic, Set, TypeVar

from src.domain.exceptions import TransicionInvalidaError
from src.domain.value_objects import EstadoLote

E = TypeVar("E", bound=Enum)


class EstadoVenta(str, Enum):
    ABIERTA = "ABIERTA"
    COMPLETADA = "COMPLETADA"


class MaquinaDeEstados(Generic[E]):
    def __init__(self, nombre: str, transiciones: Dict[E, Set[E]]):
        self.nombre = nombre
        self._transiciones = transiciones

    def destinos(self, origen: E) -> Set[E]:
        return set(self._transiciones.get(origen, set()))

    def puede(self, origen: E, destino: E) -> bool:
        return destino in self._transiciones.get(origen, set())

    def validar(self, origen: E, destino: E) -> None:
        if not self.puede(origen, destino):
            raise TransicionInvalidaError(
                f"{self.nombre}: transición no permitida {origen.value} -> {destino.value}."
            )


MAQUINA_LOTE = MaquinaDeEstados(
    "Lote",
    {
        EstadoLote.VIGENTE: {EstadoLote.CUARENTENA, EstadoLote.RETIRADO},
        EstadoLote.CUARENTENA: {EstadoLote.VIGENTE, EstadoLote.RETIRADO},
        EstadoLote.RETIRADO: set(),
    },
)

MAQUINA_VENTA = MaquinaDeEstados(
    "Venta",
    {
        EstadoVenta.ABIERTA: {EstadoVenta.COMPLETADA},
        EstadoVenta.COMPLETADA: set(),
    },
)
