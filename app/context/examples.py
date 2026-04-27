ESTIMATION_EXAMPLES = [
    {
        "meeting_summary": (
            "El cliente necesita una plataforma web de gestion de inventario para "
            "centralizar productos, controlar stock por almacen, administrar roles "
            "de usuario y consultar metricas operativas en un dashboard."
        ),
        "estimation": """
## Estimacion: Plataforma de Gestion de Inventario

### Desglose de tareas:
1. Descubrimiento funcional y refinamiento de alcance: 12 horas
2. Diseno UI/UX de flujos principales: 40 horas
3. Backend API para productos, almacenes y movimientos de stock: 64 horas
4. Autenticacion, roles y permisos: 24 horas
5. Dashboard con metricas de inventario: 32 horas
6. Testing funcional y ajustes de QA: 28 horas
7. Despliegue inicial y documentacion tecnica: 12 horas

**Total estimado: 212 horas**
**Equipo recomendado: 2 desarrolladores full-stack + 1 disenador UX part-time**
**Duracion estimada: 7-9 semanas**
**Riesgos principales: reglas de stock no cerradas, integraciones futuras con ERP**
""".strip(),
    },
    {
        "meeting_summary": (
            "El cliente solicita una aplicacion interna para gestionar solicitudes "
            "de vacaciones, aprobaciones por responsables, calendario compartido "
            "y notificaciones por email para empleados y managers."
        ),
        "estimation": """
## Estimacion: Portal Interno de Vacaciones

### Desglose de tareas:
1. Analisis de reglas de negocio y matriz de aprobaciones: 10 horas
2. Diseno de pantallas para empleados y managers: 24 horas
3. Backend API de solicitudes, estados y aprobaciones: 44 horas
4. Calendario compartido con filtros por equipo: 28 horas
5. Notificaciones por email y plantillas transaccionales: 18 horas
6. Panel de administracion basico: 22 horas
7. Testing, validacion con usuarios y correcciones: 24 horas

**Total estimado: 170 horas**
**Equipo recomendado: 1 desarrollador full-stack senior + 1 QA part-time**
**Duracion estimada: 5-7 semanas**
**Riesgos principales: reglas laborales especificas, sincronizacion con sistemas de RRHH**
""".strip(),
    },
    {
        "meeting_summary": (
            "El cliente quiere modernizar su ecommerce B2B para que distribuidores "
            "puedan consultar catalogo, precios por contrato, disponibilidad, pedidos "
            "recurrentes y estado de entregas desde un portal autoservicio."
        ),
        "estimation": """
## Estimacion: Portal Ecommerce B2B

### Supuestos principales:
- El catalogo y los precios se obtienen desde un ERP existente mediante API.
- El primer alcance incluye pedidos simples y recurrentes, sin marketplace de terceros.
- El cliente proveera reglas comerciales y plantillas de documentos.

### Desglose de tareas:
1. Descubrimiento de reglas comerciales, roles y flujos de compra: 16 horas
2. Diseno UX de catalogo, carrito, checkout y area de pedidos: 44 horas
3. Integracion con ERP para productos, precios y stock: 56 horas
4. Backend API para clientes, contratos, pedidos y recurrencias: 72 horas
5. Frontend responsive para portal de distribuidores: 68 horas
6. Notificaciones, documentos de pedido y tracking de entregas: 30 horas
7. Testing de integraciones, seguridad y regresion de compra: 42 horas
8. Despliegue, monitoreo inicial y documentacion operativa: 16 horas

**Total estimado: 344 horas**
**Equipo recomendado: 2 desarrolladores full-stack + 1 UX/UI + 1 QA part-time**
**Duracion estimada: 10-12 semanas**
**Riesgos principales: disponibilidad del ERP, reglas de precio complejas, datos de catalogo incompletos**
""".strip(),
    },
    {
        "meeting_summary": (
            "Una empresa de mantenimiento necesita una app movil para tecnicos de "
            "campo con agenda diaria, checklists offline, captura de fotos, firma "
            "del cliente y sincronizacion con el panel administrativo."
        ),
        "estimation": """
## Estimacion: App Movil para Tecnicos de Campo

### Supuestos principales:
- La app debe funcionar en Android e iOS usando una base cross-platform.
- El modo offline cubre ordenes asignadas previamente y sincroniza al recuperar conexion.
- El panel administrativo existente expone APIs o se podran agregar endpoints.

### Desglose de tareas:
1. Analisis de operativa de campo y estados de ordenes de trabajo: 14 horas
2. Diseno UX movil para agenda, checklist, evidencias y firma: 36 horas
3. Backend para asignaciones, evidencias, firmas y sincronizacion: 58 horas
4. App movil con autenticacion, agenda y detalle de orden: 64 horas
5. Soporte offline, cola de sincronizacion y resolucion de conflictos: 48 horas
6. Captura de fotos, geolocalizacion y firma digital: 34 horas
7. QA en dispositivos, escenarios sin conexion y pruebas piloto: 40 horas
8. Publicacion en stores, capacitacion y documentacion: 18 horas

**Total estimado: 312 horas**
**Equipo recomendado: 1 desarrollador mobile + 1 backend + 1 QA + 1 UX part-time**
**Duracion estimada: 9-11 semanas**
**Riesgos principales: reglas offline, calidad de conectividad, permisos de dispositivos y aprobacion de stores**
""".strip(),
    },
    {
        "meeting_summary": (
            "El cliente necesita un CRM ligero para su equipo comercial con pipeline "
            "kanban, registro de interacciones, tareas de seguimiento, importacion "
            "de leads desde CSV y reportes basicos por vendedor."
        ),
        "estimation": """
## Estimacion: CRM Comercial Ligero

### Supuestos principales:
- El CRM sera una aplicacion web interna para hasta 50 usuarios.
- La primera version no incluye automatizaciones avanzadas ni integracion telefonica.
- Los reportes se basan en datos transaccionales del propio CRM.

### Desglose de tareas:
1. Definicion de pipeline, permisos y campos de oportunidad: 12 horas
2. Diseno de vistas kanban, ficha de lead y panel de tareas: 30 horas
3. Backend API para leads, oportunidades, actividades y tareas: 54 horas
4. Frontend de pipeline drag-and-drop y busqueda avanzada: 50 horas
5. Importacion CSV con validaciones y manejo de errores: 20 horas
6. Reportes por vendedor, etapa y probabilidad de cierre: 28 horas
7. Autenticacion, roles y auditoria basica de cambios: 22 horas
8. Testing funcional, carga de datos inicial y ajustes de usabilidad: 30 horas

**Total estimado: 246 horas**
**Equipo recomendado: 2 desarrolladores full-stack + 1 QA part-time**
**Duracion estimada: 7-9 semanas**
**Riesgos principales: definicion tardia de campos comerciales, calidad de datos importados, adopcion del equipo**
""".strip(),
    },
    {
        "meeting_summary": (
            "Una direccion financiera solicita un sistema de reporting que consolide "
            "datos de ventas, gastos y facturacion desde varias fuentes, genere KPIs "
            "mensuales y permita exportar reportes para comite ejecutivo."
        ),
        "estimation": """
## Estimacion: Plataforma de Reporting Financiero

### Supuestos principales:
- Las fuentes principales entregan datos por API o archivos programados.
- El alcance inicial cubre KPIs mensuales, no analitica predictiva.
- Los usuarios validadores estaran disponibles para reconciliacion de cifras.

### Desglose de tareas:
1. Levantamiento de fuentes, definiciones de KPI y reglas de reconciliacion: 20 horas
2. Diseno de modelo de datos y estrategia de carga incremental: 28 horas
3. Pipelines de ingesta para ventas, gastos y facturacion: 66 horas
4. Backend para consultas agregadas, permisos y auditoria: 42 horas
5. Dashboard ejecutivo con filtros, comparativas y tendencias: 48 horas
6. Exportacion a Excel/PDF y plantillas de reportes: 24 horas
7. Validacion de datos, pruebas de consistencia y alertas de carga: 38 horas
8. Despliegue, documentacion y transferencia al equipo financiero: 18 horas

**Total estimado: 284 horas**
**Equipo recomendado: 1 data engineer + 1 desarrollador full-stack + 1 QA/data analyst part-time**
**Duracion estimada: 8-10 semanas**
**Riesgos principales: discrepancias entre fuentes, acceso a datos historicos, definiciones cambiantes de KPI**
""".strip(),
    },
]
