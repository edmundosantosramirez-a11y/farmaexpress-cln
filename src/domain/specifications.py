"""Specification pattern: reglas de negocio como objetos componibles.

Cada especificación responde a una regla del BRD/U3:
  RN-01/RN-04  LoteConExistencia
  RN-02        LoteNoCaducado
  RN-03        LoteNoRetirado (y LoteNoEnCuarentena)
  RN-06        VentaConRecetaCompleta
  RN-08        ExistenciaBajoMinimo
  RN-09        LoteProximoACaducar
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from src.domain.value_objects import EstadoLote


class Specification(ABC):
    """Contrato base. Se combinan con &, | y ~."""

    @abstractmethod
    def is_satisfied_by(self, candidato) -> bool:
        ...

    def motivo_rechazo(self, candidato) -> Optional[str]:
        """None si se cumple; si no, el texto de la primera regla que falla."""
        return None if self.is_satisfied_by(candidato) else self.mensaje

    mensaje: str = "No cumple la especificación."

    def __and__(self, otra: "Specification") -> "Specification":
        return AndSpecification(self, otra)

    def __or__(self, otra: "Specification") -> "Specification":
        return OrSpecification(self, otra)

    def __invert__(self) -> "Specification":
        return NotSpecification(self)


class AndSpecification(Specification):
    def __init__(self, izquierda: Specification, derecha: Specification):
        self.izquierda = izquierda
        self.derecha = derecha

    def is_satisfied_by(self, candidato) -> bool:
        return self.izquierda.is_satisfied_by(candidato) and self.derecha.is_satisfied_by(candidato)

    def motivo_rechazo(self, candidato) -> Optional[str]:
        return self.izquierda.motivo_rechazo(candidato) or self.derecha.motivo_rechazo(candidato)


class OrSpecification(Specification):
    def __init__(self, izquierda: Specification, derecha: Specification):
        self.izquierda = izquierda
        self.derecha = derecha

    def is_satisfied_by(self, candidato) -> bool:
        return self.izquierda.is_satisfied_by(candidato) or self.derecha.is_satisfied_by(candidato)

    def motivo_rechazo(self, candidato) -> Optional[str]:
        if self.is_satisfied_by(candidato):
            return None
        return f"{self.izquierda.motivo_rechazo(candidato)} / {self.derecha.motivo_rechazo(candidato)}"


class NotSpecification(Specification):
    def __init__(self, spec: Specification):
        self.spec = spec
        self.mensaje = "Se cumple una condición que no debía cumplirse."

    def is_satisfied_by(self, candidato) -> bool:
        return not self.spec.is_satisfied_by(candidato)


# ---------- Especificaciones sobre Lote ----------

class LoteNoCaducado(Specification):
    """RN-02: un lote cuya fecha de caducidad ya llegó no es vendible."""

    def __init__(self, fecha_actual: date):
        self.fecha_actual = fecha_actual
        self.mensaje = "Lote caducado."

    def is_satisfied_by(self, lote) -> bool:
        return lote.fecha_caducidad > self.fecha_actual


class LoteNoRetirado(Specification):
    """RN-03: un lote retirado no se vende en ninguna sucursal."""
    mensaje = "Lote retirado."

    def is_satisfied_by(self, lote) -> bool:
        return lote.estado != EstadoLote.RETIRADO


class LoteNoEnCuarentena(Specification):
    """Glosario: la cuarentena aparta el lote de la venta mientras se revisa."""
    mensaje = "Lote en cuarentena."

    def is_satisfied_by(self, lote) -> bool:
        return lote.estado != EstadoLote.CUARENTENA


class LoteConExistencia(Specification):
    """RN-04: sin existencia suficiente no se vende (RN-01: control por lote)."""

    def __init__(self, cantidad: int = 1):
        self.cantidad = cantidad
        self.mensaje = "Existencia insuficiente en el lote."

    def is_satisfied_by(self, lote) -> bool:
        return lote.stock >= self.cantidad and lote.stock > 0


class LoteVendible(Specification):
    """Composición de RN-02, RN-03 y RN-04. El orden define el motivo reportado."""

    def __init__(self, fecha_actual: date, cantidad: int = 1):
        self._spec = (
            LoteNoRetirado()
            & LoteNoEnCuarentena()
            & LoteNoCaducado(fecha_actual)
            & LoteConExistencia(cantidad)
        )

    def is_satisfied_by(self, lote) -> bool:
        return self._spec.is_satisfied_by(lote)

    def motivo_rechazo(self, lote) -> Optional[str]:
        return self._spec.motivo_rechazo(lote)


class LoteProximoACaducar(Specification):
    """RN-09: lote vigente que caduca dentro de `dias` días (umbrales 90/60/30)."""

    def __init__(self, fecha_actual: date, dias: int = 90):
        self.fecha_actual = fecha_actual
        self.dias = dias
        self.mensaje = f"El lote no caduca en los próximos {dias} días."

    def is_satisfied_by(self, lote) -> bool:
        restantes = (lote.fecha_caducidad - self.fecha_actual).days
        return 0 < restantes <= self.dias


# ---------- Especificaciones sobre existencia y Venta ----------

class ExistenciaBajoMinimo(Specification):
    """RN-08: la existencia (un entero) cae por debajo de la existencia mínima."""

    def __init__(self, existencia_minima: int):
        self.existencia_minima = existencia_minima
        self.mensaje = "La existencia no está por debajo del mínimo."

    def is_satisfied_by(self, existencia: int) -> bool:
        return existencia < self.existencia_minima


class VentaConRecetaCompleta(Specification):
    """RN-06: si algún producto exige receta, debe haber receta registrada."""
    mensaje = "Medicamentos controlados requieren receta."

    def is_satisfied_by(self, venta) -> bool:
        exige = any(linea.requiere_receta for linea in venta.lineas)
        return (not exige) or venta.receta is not None


class VentaConProductos(Specification):
    mensaje = "No se puede completar una venta sin productos."

    def is_satisfied_by(self, venta) -> bool:
        return len(venta.lineas) > 0
