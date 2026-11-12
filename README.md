# FarmaExpress - Componentes de Lógica de Negocio (PIA)

Solución integral de punto de venta e inventario farmacéutico basada en **Domain-Driven Design (DDD)**, **Specification Pattern**, **State Machine** y **FastAPI**.

---

## Despliegue en Producción (Render)

| Componente | Descripción | Enlace Directo |
| :--- | :--- | :--- |
| **Interfaz Web (Frontend)** | Punto de venta e inventario visual | [Abrir Aplicación Web](https://farmaexpress-api-g3on.onrender.com/app) |
| **API Docs (Swagger UI)** | Documentación interactiva y pruebas de endpoints | [Abrir Swagger UI](https://farmaexpress-api-g3on.onrender.com/docs) |
| **Estado de Persistencia** | Verifica conexión activa con PostgreSQL | [Ver Persistencia](https://farmaexpress-api-g3on.onrender.com/info) |
| **Health Check** | Monitoreo de disponibilidad del servidor | [Ver Salud del Servidor](https://farmaexpress-api-g3on.onrender.com/health) |

> **Nota:** Al estar alojado en una instancia gratuita de Render, la primera petición tras un periodo de inactividad puede tardar aproximadamente 50 segundos en despertar el servidor.

---

## Arquitectura y Tecnologías

* **Backend:** Python 3.11, FastAPI y Uvicorn
* **Base de Datos:** PostgreSQL (con respaldo automático en memoria para pruebas)
* **Frontend:** HTML5, CSS3 y JavaScript integrado en `src/api/static/index.html`
* **Patrones aplicados:** DDD, Specification Pattern, State Machine y Repository Pattern

---

## Ejecución Local (Desarrollo)

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/edmundosantosramirez-a11y/farmaexpress-cln.git](https://github.com/edmundosantosramirez-a11y/farmaexpress-cln.git)
   cd farmaexpress-cln
