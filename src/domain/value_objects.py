from dataclasses import dataclass
from enum import Enum
from datetime import date
from typing import Optional
from src.domain.exceptions import DatosDeRecetaIncompletosError

class EstadoLote(str, Enum):
    VIGENTE = "VIGENTE"
    CUARENTENA = "CUARENTENA"
    RETIRADO = "RETIRADO"

@dataclass(frozen=True)
class RecetaMedica:
    folio: str
    cedula_medico: str
    nombre_medico: str
    fecha_emision: Optional[date] = None

    def __post_init__(self):
        if not self.folio or not self.cedula_medico or not self.nombre_medico:
            raise DatosDeRecetaIncompletosError("Cédula, nombre del médico y folio son obligatorios.")
        if len(self.cedula_medico.strip()) < 6:
            raise DatosDeRecetaIncompletosError("Cédula profesional inválida.")
