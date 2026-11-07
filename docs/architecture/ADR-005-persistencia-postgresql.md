# ADR-005: Persistencia con PostgreSQL, Repository y Unit of Work

**Estado:** propuesto (pendiente de validar con el equipo)

## Contexto
U3 dejó los repositorios como interfaces con implementación en memoria "solo para validar la arquitectura".
El PIA exige base de datos, Docker Compose con DB + App + Tests y 12-Factor. Además, U3 pide que
`completarVenta` sea una sola transacción (ticket + descuento de existencia) y control de concurrencia optimista en Lote.

## Decisión
- PostgreSQL con SQLAlchemy. Los modelos (`infrastructure/models.py`) están separados del dominio; los repositorios
  mapean en ambos sentidos y el dominio no depende de SQL (U3, validación "Persistencia").
- `SqlUnitOfWork`: una sesión = una transacción por petición. Si un caso de uso falla antes de `commit`, no se persiste nada.
- Concurrencia optimista: columna `version` en `lotes` (`version_id_col`). Dos cajas que descuentan el mismo lote
  al mismo tiempo: la segunda recibe conflicto (HTTP 409).
- Catálogo de productos (`productos`): precio y obligación de receta salen del catálogo, no del cajero.
- Configuración por variables de entorno (`DATABASE_URL`). Sin esa variable la API usa memoria (pruebas unitarias).
- Las tablas se crean al iniciar (`create_all`). No se usan migraciones en esta iteración.

## Alternativas consideradas
- Solo repositorios en memoria: no cumple el PIA y pierde los datos al reiniciar.
- Consistencia eventual con compensaciones: descartada en U3 porque el producto ya salió del mostrador.
- Migraciones con Alembic: se pospone; `create_all` basta para la demostración.

## Consecuencias
- (+) Los datos persisten, la transacción de venta es atómica y las pruebas de integración corren contra PostgreSQL.
- (-) El dominio actual no modela existencia por sucursal (un Lote tiene un solo stock); queda como mejora.
- (-) La base gratuita de Render expira a los 30 días.
