#  FarmaExpress - Componentes de Lógica de Negocio (PIA)

Solución integral de punto de venta e inventario farmacéutico basada en **Domain-Driven Design (DDD)**, **Specification Pattern**, **State Machine** y **FastAPI**[cite: 11].

---

##  Despliegue en Producción (Render)

| Componente | Descripción | Enlace Directo |
| :--- | :--- | :--- |
| **Interfaz Web (Frontend)** | Punto de venta e inventario visual | [Abrir Aplicación Web](https://farmaexpress-api-g3on.onrender.com/app) |
| **API Docs (Swagger UI)** | Documentación interactiva y pruebas de endpoints | [Abrir Swagger UI](https://farmaexpress-api-g3on.onrender.com/docs)[cite: 11] |
| **Estado de Persistencia** | Verifica conexión activa con PostgreSQL | [Ver Persistencia](https://farmaexpress-api-g3on.onrender.com/info)[cite: 5] |
| **Health Check** | Monitoreo de disponibilidad del servidor | [Ver Salud del Servidor](https://farmaexpress-api-g3on.onrender.com/health)[cite: 11] |

> **Nota:** Al estar alojado en una instancia gratuita de Render, la primera petición tras un periodo de inactividad puede tardar ~50 segundos en despertar el servidor[cite: 7, 9].

---

##  Arquitectura y Tecnologías

* **Backend:** Python 3.11 + FastAPI + Uvicorn[cite: 8]
* **Base de Datos:** PostgreSQL (con respaldo automático en memoria para pruebas)[cite: 5]
* **Frontend:** HTML5 / CSS3 / JavaScript integrado en `src/api/static/index.html`[cite: 5]
* **Patrones aplicados:** DDD, Specification Pattern, State Machine y Repository Pattern[cite: 5, 11].

---

##  Ejecución Local (Desarrollo)

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/edmundosantosramirez-a11y/farmaexpress-cln.git](https://github.com/edmundosantosramirez-a11y/farmaexpress-cln.git)
   cd farmaexpress-cln
