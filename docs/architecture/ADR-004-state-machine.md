# ADR-004: Máquina de estados para Lote y Venta

**Estado:** propuesto. Los supuestos marcados deben validarse con el cliente.

## Contexto
El glosario define estados con consecuencias (cuarentena, retiro de lote, ticket inmutable). Antes, el estado
del lote se cambiaba sin validar el origen (por ejemplo, `retirar` o `poner_en_cuarentena` desde cualquier estado)
y la venta usaba una bandera booleana `completada`.

## Decisión
`src/domain/state_machine.py` define las transiciones permitidas y toda transición pasa por `MaquinaDeEstados.validar`:

- Lote: VIGENTE -> CUARENTENA | RETIRADO; CUARENTENA -> VIGENTE | RETIRADO; RETIRADO -> (ninguna).
- Venta: ABIERTA -> COMPLETADA; COMPLETADA -> (ninguna).

Una transición no permitida lanza `TransicionInvalidaError` (la API responde 422). "Caducado" no es un estado:
se deduce de la fecha (U3, Etapa 3).

## Supuestos (el BRD no los define)
- Un lote retirado es irreversible (U3, Etapa 5; H05 propone reactivación por el Responsable, pendiente).
- La cuarentena puede liberarse; el glosario la define como temporal.
- Cancelar una venta cobrada queda fuera (hallazgo sobre permisos de cancelación).

## Alternativas consideradas
- Subtipos de Lote (LoteRetirado heredando de Lote): descartado en la revisión SOLID (U3, principio L).
- Bandera booleana: no impide transiciones ilegales.

## Consecuencias
- (+) Las transiciones ilegales se rechazan en un único lugar y son fáciles de demostrar.
- (-) Si el cliente define más estados (p. ej. cancelada), se amplía la tabla de transiciones.
