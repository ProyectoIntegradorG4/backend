# Diseño de experimento

---

# Experimento de Registro de Clientes Institucionales desde APP Móvil con Validación NIT (Lista Blanca)

## Propósito del experimento

Validar que el tiempo de respuesta (latencia) se mantiene por debajo de 1 segundo al introducir la validación tributaria (NIT) contra la tabla InstitucionesAsociadas y controles de seguridad (Asignación de un rol por defecto para clientes institucionales) en el servicio de registro de clientes institucionales desde APP Móvil desarrollada en React Native, Backend Python FastAPI. El experimento medirá la latencia en una primera versión sin validación y luego en una versión con validación completa, comparando resultados para verificar la viabilidad técnica de la arquitectura propuesta.

## Resultados esperados

### Resultados Técnicos
- **Latencia Comparativa**: Medir diferencia de latencia entre versión sin validación vs versión con validación NIT completa y asignacion de ROL usuario Institucional.
- **Umbral de Latencia**: Mantener tiempo de respuesta <1 segundo en versión con validación NIT contra InstitucionesAsociadas
- **Funcionalidad**: Implementar flujo de registro con 4 campos (nombre, correo, NIT, contraseña) y validación automática.
- **Arquitectura**: Validar integración eficiente entre React Native y User Management Service con validación NIT y asignacion de rol.

### Resultados de Negocio (basados en HU-MOV-007)
- **Registro exitoso**: 100% de representantes (Clientes) institucionales con NIT válido pueden completar registro y recibir confirmación desde la app
- **Validación NIT**: 100% de NIT no registrados en InstitucionesAsociadas son rechazados con mensaje específico
- **Asignación de roles**: 100% de usuarios con NIT válido reciben automáticamente rol de usuario institucional
- **Asociación institucional**: 100% de usuarios quedan asociados correctamente con institución y país correspondiente

### Resultados de Calidad
- **Usabilidad**: Confirmar que la interfaz es intuitiva para usuarios de instituciones de salud sin capacitación técnica.
- **Seguridad**: Implementar autenticación segura y control de acceso basado en roles.
- **Disponibilidad**: 99% de disponibilidad durante pruebas de registro.

## Recursos requeridos

**Software:**
- React Native 0.72 con Expo SDK
- Visual Studio Code con extensiones React Native
- Node.js 18+, npm/yarn
- Android Studio (emuladores Android)
- Uso de Expo Go (App para probar las aplicaciones en React Native)
- Xcode (simuladores iOS - opcional)

**Backend y Servicios:**
- FastAPI (Python) para microservicios
- PostgreSQL para base de datos
- Redis para caché
- Docker para contenedores

**Hardware:**
- Dispositivos móviles Android/iOS para pruebas reales
- Máquinas de desarrollo con 16GB RAM mínimo

<!--
**Librerías específicas:**
- React Navigation para navegación
- AsyncStorage para persistencia local
- Axios para comunicación HTTP
- react-hook-form para manejo de formularios
- React Native Paper para componentes UI
-->

## Elementos de arquitectura involucrados

**ASR Asociados:**
- **Latencia** (Escenario 4): Registro de clientes institucionales con validación NIT en <1 segundo 99.95% de las veces
- **Seguridad** (Escenario 2): Validación controlada contra InstitucionesAsociadas con auditoría 100% de las veces
- **Usabilidad** (Escenario 2): Interfaz intuitiva para formulario de 4 campos

**Elementos de Arquitectura:**
- **Vista Funcional**: User Management Service con validación NIT integrada
- **Vista de Información**: Flujo de datos entre app móvil, User Management Service y tabla InstitucionesAsociadas
- **Vista de Despliegue**: Aplicación móvil React Native, contenedor User Management Service
- **Vista de Concurrencia**: Procesamiento asíncrono de validaciones NIT y asignación de roles

**Puntos de Sensibilidad:**
- Tiempo de respuesta de consulta y Validacion a tabla InstitucionesAsociadas
- Impacto de validación NIT en latencia total del registro
- Capacidad de React Native para manejar formulario de 4 campos con validación en tiempo real
- Correcta asignación automática de roles y asociación institucional

**Modelo de Datos Requerido:**

```sql
-- Tabla InstitucionesAsociadas

CREATE TABLE InstitucionesAsociadas (
    nit VARCHAR(20) PRIMARY KEY,
    nombre_institucion VARCHAR(255) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla Usuarios (modificada para incluir asociación institucional)
CREATE TABLE Usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    correo_electronico VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nit VARCHAR(20) NOT NULL,
    rol VARCHAR(50) DEFAULT 'usuario_institucional',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);
```

## Interpretación de resultados

### Criterios de Éxito (Experimento Exitoso)
- **Latencia Comparativa**: Diferencia <300ms entre versión sin validación vs con validación NIT
- **Umbral Absoluto**: Registro completo con validación NIT en <1 segundo en 95% de casos
- **Funcionalidad**: 100% de NIT válidos en InstitucionesAsociadas permiten registro exitoso
- **Asignación Roles**: 100% de usuarios registrados reciben automáticamente rol institucional
- **Asociación**: 100% de usuarios quedan correctamente asociados con institución y país
- **Usabilidad**: Formulario de 4 campos completable en <30 segundos por usuario promedio

### Criterios de Ajuste Parcial (Requiere Optimización)
- **Latencia**: Registro en 1-2 segundos → optimizar caché Redis, reducir payloads
- **Funcionalidad**: 80-95% criterios cumplidos → ajustar validaciones, mejorar UX
- **Usabilidad**: Formulario en 30-60 segundos → simplificar campos, mejorar feedback
- **Seguridad**: 95-99% validaciones correctas → refinar lista blanca, mejorar algoritmos
- **Disponibilidad**: 95-99% solicitudes exitosas → ajustar timeouts, mejorar error handling

### Criterios de Fallo (Replantear Arquitectura)
- **Latencia**: Registro >2 segundos → React Native no viable, considerar web móvil
- **Funcionalidad**: <80% criterios cumplidos → arquitectura inadecuada para dominio
- **Usabilidad**: Formulario >60 segundos → interfaz inutilizable para usuarios objetivo
- **Seguridad**: <95% validaciones correctas → riesgo inaceptable para sector salud
- **Disponibilidad**: <95% solicitudes exitosas → arquitectura no confiable

## Plan Experimental con Fases

### Fase 1: Implementación Base (8 horas)
**Objetivo**: Desarrollar versión sin validación NIT para establecer línea base de latencia
- Implementar formulario React Native con 4 campos (nombre, correo, NIT, contraseña)
- Desarrollar User Management Service básico sin validación NIT
- Configurar base de datos con tabla Usuarios básica
- **Métricas a medir**: Latencia de registro sin validación (p50, p95, p99)

### Fase 2: Implementación con Validación NIT (12 horas)
**Objetivo**: Integrar validación contra InstitucionesAsociadas y medir impacto en latencia
- Crear tabla InstitucionesAsociadas con datos de prueba
- Implementar validación NIT en User Management Service
- Integrar asignación automática de roles y asociación institucional
- **Métricas a medir**: Latencia de registro con validación completa (p50, p95, p99)

### Fase 3: Optimización y Comparación (8 horas)
**Objetivo**: Optimizar performance y generar reporte comparativo
- Implementar caché Redis para consultas frecuentes a InstitucionesAsociadas
- Optimizar queries de base de datos con índices apropiados
- Ejecutar pruebas de carga comparativas entre Fase 1 y Fase 2
- **Entregable**: Reporte de latencia comparativa con recomendaciones

### Criterios de Transición entre Fases
- **Fase 1 → Fase 2**: Latencia base <500ms establecida y documentada
- **Fase 2 → Fase 3**: Funcionalidad completa implementada, latencia medida
- **Finalización**: Diferencia de latencia documentada y dentro de umbrales aceptables

## Métricas de validación específicas

### Métricas Técnicas Comparativas
- **Latencia Fase 1 (sin validación)**: Registro básico (p50, p95, p99)
- **Latencia Fase 2 (con validación)**: Registro con validación NIT (p50, p95, p99)
- **Diferencia de latencia**: Impacto de validación NIT en tiempo total
- **Latencia consulta InstitucionesAsociadas**: <200ms (p95)
- **Concurrencia**: 10 usuarios simultáneos sin degradación >10%

### Métricas de Negocio (HU-MOV-007)
- **Tasa de registro exitoso**: 100% con NIT válido en InstitucionesAsociadas
- **Tasa de rechazo NIT inválido**: 100% con mensaje específico "NIT no autorizado"
- **Asignación correcta de roles**: 100% usuarios reciben rol "usuario_institucional"
- **Asociación institucional**: 100% usuarios asociados con institución y país correcto
- **Tiempo completar formulario**: <30 segundos (4 campos)
- **Tiempo mostrar confirmación**: <1s después de registro exitoso

### Métricas de Calidad
- **Cobertura de pruebas**: >80%
- **Tiempo de respuesta UI**: <100ms para interacciones
- **Tasa de errores de red**: <1%
- **Satisfacción de usuario**: >4/5 en pruebas de usabilidad

## Matriz de Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación | Responsable |
|--------|--------------|---------|------------|-------------|
| **Latencia de validación NIT excede 1s** | Media | Alto | Implementar caché Redis, optimizar queries con índices, considerar validación asíncrona | Wilson Aponte |
| **Tabla InstitucionesAsociadas con datos insuficientes** | Baja | Alto | Preparar dataset de prueba con 100+ instituciones reales, validar integridad de datos | Julio César Forero |
| **Fallo en asignación automática de roles** | Baja | Medio | Implementar transacciones ACID, pruebas unitarias exhaustivas, rollback automático | Wilson Aponte |
| **React Native no maneja formulario 4 campos eficientemente** | Baja | Medio | Validación incremental, optimización de renders, uso de React | Julio César Forero |
| **Consultas concurrentes degradan performance** | Media | Alto | Pool de conexiones optimizado, monitoreo de queries lentas, límites de concurrencia | Wilson Aponte |
| **Diferencia latencia Fase 1 vs Fase 2 >300ms** | Media | Alto | Optimización de queries, caché inteligente, revisión de arquitectura | Ambos |
| **Datos de prueba no representativos** | Media | Medio | Usar datos reales anonimizados, validar con stakeholders de negocio | Julio César Forero |

## Plan de pruebas detallado

### Pruebas Unitarias (16 horas)
- **React Native Components**: Formulario, validaciones, navegación
- **Microservicios**: User Management, Nit Service (NIT válidos en InstitucionesAsociadas), Audit Service
- **APIs**: Endpoints de registro, validación, autenticación
- **Base de datos**: Queries, transacciones, constraints

### Pruebas de Integración (8 horas)
- **Flujo completo**: App móvil → API Gateway → Microservicios → BD
- **Validación NIT**: Lista blanca → Cache → Respuesta
- **Autenticación**: JWT → Refresh tokens → Sesiones
- **Auditoría**: Logging → Trazabilidad → Reportes

### Pruebas de Usabilidad (4 horas)
- **Dispositivos reales**: Android (1 modelo) + iOS (1 modelo)
- **Escenarios de usuario**: Registro exitoso con confirmación desde la app, error NIT, duplicado
- **Métricas UX**: Tiempo completar, errores usuario, satisfacción, tiempo mostrar confirmación
- **Accesibilidad**: Lectores de pantalla, contraste, navegación

### Pruebas de Performance (4 horas)
- **Carga**: 10 usuarios simultáneos registrándose
- **Estrés**: 50 usuarios concurrentes
- **Latencia**: Medición end-to-end con herramientas
- **Memoria**: Uso de recursos en dispositivos móviles

## Criterios de aceptación por funcionalidad

### Mobile App (React Native)
- **Formulario de registro**: Renderizado en <500ms, validación en tiempo real
- **Navegación**: Transiciones fluidas <200ms entre pantallas
- **Persistencia local**: AsyncStorage funcional para tokens y caché
- **Manejo de errores**: Mensajes claros y específicos para cada tipo de error
- **Confirmación de registro**: Pantalla de confirmación mostrada <1s después de registro exitoso
- **Offline handling**: Funcionalidad básica sin conectividad

### User Management Service
- **Creación de usuario**: <1s para registro completo
- **Validación de roles**: Asignación automática de rol "cliente institucional"
- **Gestión de sesiones**: JWT tokens con refresh automático
- **Prevención duplicados**: Detección 100% de instituciones ya registradas
 
### API Gateway
- **Rate limiting**: 100 requests/minuto por IP
- **Autenticación**: Validación JWT <100ms
- **Routing**: Latencia adicional <50ms por request
- **CORS**: Configuración correcta para React Native

### Audit Service
- **Logging**: Registro de eventos <100ms
- **Trazabilidad**: Correlación de eventos por session_id
- **Retención**: Datos auditables.
- **Reportes**: Generación de reportes de seguridad

<!-- ## Estrategia de rollback

### Rollback Automático
- **Trigger**: Error rate >5% durante 5 minutos consecutivos
- **Acción**: Desactivar endpoint de registro móvil automáticamente
- **Notificación**: Alertas inmediatas al equipo de desarrollo
- **Fallback**: Redirección a versión web de registro

### Rollback Manual
- **Trigger**: Decisiones de negocio o problemas de seguridad
- **Procedimiento**: 
  1. Desactivar feature flag de registro móvil
  2. Notificar usuarios vía push notification
  3. Migrar datos pendientes a sistema web
  4. Comunicar a stakeholders

### Plan de Contingencia
- **Versión web**: Mantener funcionalidad de registro web como backup
- **Migración de datos**: Scripts para transferir registros móviles a web
- **Comunicación**: Plan de comunicación a usuarios afectados
- **Recuperación**: Procedimiento para reactivar móvil post-corrección -->

## Monitoreo y alertas

### Métricas de Monitoreo
- **Latencia**: p50, p95, p99 de registro completo
- **Throughput**: Registros por minuto, requests por segundo
- **Errores**: Rate de errores por endpoint, tipos de error
- **Disponibilidad**: Uptime de microservicios, conectividad móvil
- **Recursos**: CPU, memoria, conexiones BD por servicio

### Alertas Críticas
- **Latencia alta**: p95 >1 segundo por 5 minutos
- **Error rate**: >5% de requests fallidos por 5 minutos
- **Disponibilidad**: Servicio down por >2 minutos
- **Cache miss**: Redis hit rate <80% por 10 minutos
- **BD connections**: Pool de conexiones >90% por 5 minutos

### Dashboards
- **Operacional**: Latencia, throughput, errores en tiempo real
- **Negocio**: Registros exitosos, abandono de formularios, satisfacción
- **Técnico**: Recursos de infraestructura, logs de aplicación
- **Móvil**: Performance de app, crashes, uso de memoria

## Documentación de APIs

### OpenAPI/Swagger
- **User Management API**: Endpoints de registro, autenticación, gestión de usuarios
- **Validación NIT (NIT Validation API)**: Validación NIT contra InstitucionesAsociadas
- **Audit API**: Logging de eventos, reportes de seguridad
<!-- - **Mobile API**: Endpoints específicos para React Native -->

### Contratos de API
- **Request/Response schemas**: Estructura de datos para cada endpoint
- **Códigos de error**: Mapeo de errores HTTP a mensajes de usuario
- **Autenticación**: Flujo JWT, refresh tokens, manejo de sesiones
- **Rate limiting**: Límites por endpoint, headers de respuesta

### Especificaciones Técnicas
- **Endpoints móviles**: URLs, métodos HTTP, parámetros
- **Validaciones**: Reglas de negocio, formatos de datos
- **Seguridad**: Headers requeridos, certificados, CORS
- **Versionado**: Estrategia de versionado de APIs

## Esfuerzo estimado

**Total**: 32 horas hombre (16 horas por integrante - 2 integrantes)
- Fase 1 - Implementación base: 8 horas
- Fase 2 - Validación NIT integrada: 12 horas  
- Fase 3 - Optimización y comparación: 8 horas
- Pruebas completas y despliegue de servicios: 4 horas

---

# Hipótesis de diseño

La implementación de validación NIT contra la tabla InstitucionesAsociadas en el User Management Service mantendrá el tiempo de respuesta del registro de clientes institucionales por debajo de 1 segundo, con una diferencia de latencia menor a 300ms comparado con una versión sin validación, demostrando la viabilidad técnica de la arquitectura propuesta para el dominio de suministros médicos.

# Punto de sensibilidad

**Principal**: Tiempo de respuesta del proceso completo de registro y validación de NIT contra lista blanca desde la aplicación móvil React Native hasta los microservicios backend.

**Secundarios**: 
- Facilidad de desarrollo para equipo sin experiencia en React Native
- Calidad de experiencia de usuario en dispositivos móviles reales
- Robustez de la validación de seguridad y gestión de roles

# Historia de arquitectura asociada

**HU-MOV-007**: Como Cliente Institucional quiero registrarme en la aplicación móvil para acceder a los servicios de autogestión y realizar pedidos.

**Criterios de Aceptación del Experimento**:
- **Registro exitoso**: Formulario completo con información válida → cuenta creada + confirmación desde la app + acceso a servicios
- **Validación de datos**: NIT/RUC inválido → mensaje error específico + formulario no se envía + solicitud corrección
- **Verificación duplicados**: Institución ya registrada → mensaje "Institución ya registrada" + opción recuperar credenciales + contacto administrador

# Nivel de incertidumbre

**Alto** - Ningún integrante del equipo tiene experiencia previa con React Native, y los requisitos de latencia y seguridad son críticos para el dominio de suministros médicos.

---

# Estilos de Arquitectura asociados al experimento

**Microservicios**: Separación de responsabilidades entre gestión de usuarios, validación tributaria y auditoría.

**Cliente-Servidor**: Aplicación móvil React Native como cliente, microservicios FastAPI como servidores.

**Capas**: Separación entre presentación (React Native UI), lógica de negocio (validación y gestión de roles) y persistencia (PostgreSQL).

# Análisis (Atributos de calidad que favorece y desfavorece)

**Favorece:**
- **Latencia**: Comunicación directa HTTP/REST entre móvil y microservicios
- **Usabilidad**: React Native permite UI nativa con desarrollo JavaScript familiar
- **Modificabilidad**: Microservicios permiten cambios independientes en validación tributaria
- **Portabilidad**: React Native despliega en iOS y Android con mismo código

**Desfavorece:**
- **Seguridad**: Aplicación móvil como cliente puede ser menos segura que web
- **Disponibilidad**: Dependencia de conectividad móvil para validación en tiempo real
- **Performance**: Overhead de React Native vs desarrollo nativo puro

---

# Tácticas de Arquitectura asociadas al experimento

**Latencia:**
- Caché local de validaciones recientes con AsyncStorage
- Compresión de payloads HTTP
- Validación asíncrona no bloqueante de UI

**Seguridad:**
- Autenticación basada en JWT con refresh tokens
- Validación de entrada en cliente y servidor
- Comunicación HTTPS obligatoria
- Sanitización de datos de entrada

**Usabilidad:**
- Validación en tiempo real con feedback inmediato
- Mensajes de error claros y específicos
- Indicadores de progreso durante validación
- Formularios con validación incremental

---

# Listado de componentes (Microservicios) involucrados en el experimento

| Microservicio | Propósito y comportamiento esperado | Tecnología Asociada |
| --- | --- | --- |
| **API Gateway** | Enrutamiento de peticiones, autenticación JWT, rate limiting | FastAPI + Nginx |
| **User Management Service** | Gestión de registro, roles y perfiles de usuarios institucionales | FastAPI + SQLAlchemy + PostgreSQL |
| **NIT Validation Service** | Validación de NIT contra lista blanca, consultas a NIT válidos en InstitucionesAsociadas | FastAPI + Redis Cache + PostgreSQL |
| **Audit Service** | Registro de eventos de seguridad, trazabilidad de acciones | FastAPI + PostgreSQL |
| **Mobile App** | Interfaz de usuario, formularios de registro, gestión de estado local | React Native + Expo + AsyncStorage |

---

# Listado de conectores involucrados en el experimento

| Conector | Comportamiento deseado en el experimento | Tecnología Asociada |
| --- | --- | --- |
| **HTTP/REST API** | Comunicación entre móvil y API Gateway con latencia <1 segundo | Axios + JSON |
| **Database Connector** | Acceso a datos de usuarios y lista blanca con transacciones ACID | SQLAlchemy + PostgreSQL |
| **Cache Connector** | Almacenamiento temporal de validaciones para mejorar latencia | Redis Client + JSON |
| **Local Storage** | Persistencia local de datos de sesión y caché en móvil | AsyncStorage + React Native |

---

| Tecnología asociada con el experimento (Desarrollo, infraestructura, almacenamiento) | Justificación |
| --- | --- |
| **Lenguajes de programación** - JavaScript/TypeScript, Python | JavaScript para React Native (requerido), Python para microservicios (equipo familiarizado) |
| **Plataforma de despliegue** - Docker + Local/AWS | Contenedores para microservicios, desarrollo local inicial |
| **Bases de datos** - PostgreSQL, Redis | PostgreSQL para datos persistentes ACID, Redis para caché de latencia |
| **Herramientas de análisis** - React Native Flipper (prueba), FastAPI Profiler | Debugging y análisis de performance específicos para el stack |
| **Librerías** - Expo SDK, React Navigation, Axios, SQLAlchemy | Expo acelera desarrollo móvil, otras son estándar para stack elegido |
| **Frameworks de desarrollo** - React Native + Expo, FastAPI | React Native objetivo del experimento, FastAPI para APIs rápidas |

---

# Distribución de actividades por integrante

| Integrante | Tareas a realizar | Esfuerzo Estimado |
| --- | --- | --- |
| **Julio César Forero** | Desarrollo React Native: formulario 4 campos, navegación, integración con User Management Service, pruebas de usabilidad, preparación datos de prueba InstitucionesAsociadas | 14 horas |
| **Wilson Aponte** | Desarrollo User Management Service: validación NIT, asignación roles, asociación institucional, optimización BD, implementación caché Redis, análisis comparativo de latencia | 14 horas |
