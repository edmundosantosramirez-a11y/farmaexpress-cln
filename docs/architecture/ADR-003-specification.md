# ADR-003: Reglas de venta de lotes como Specifications

**Estado:** propuesto (pendiente de validar con el equipo)

## Contexto
El BRD (§6, §8) exige cero ventas de lotes caducados o retirados, y las reglas RN-02, RN-03, RN-04, RN-06, RN-08 y RN-09
se evalúan en varios casos de uso. Antes, esas condiciones estaban repetidas con `if` dentro de `Lote` y `Venta`,
y `validar_dispensacion` no revisaba la cuarentena aunque `es_vendible` sí.

## Decisión
Aplicar el patrón Specification (`src/domain/specifications.py`): cada regla es un objeto con `is_satisfied_by`,
combinable con `&`, `|` y `~`. `LoteVendible` compone RN-02, RN-03 y RN-04 y expone `motivo_rechazo`.
`Lote.es_vendible` y `Lote.validar_dispensacion` usan las mismas especificaciones.

## Alternativas consideradas
- `if` dentro de las entidades (estado anterior): reglas duplicadas, difícil de probar por separado.
- Validar en los Handlers: las reglas saldrían del dominio, contra la decisión de Domain Model de U3.

## Consecuencias
- (+) Cada regla se prueba sola y se traza a su RN-xx.
- (+) Las reglas abiertas (umbral 90/60/30, existencia mínima) se cambian sin tocar los casos de uso.
- (-) Más clases pequeñas.
