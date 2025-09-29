# Colección de Postman - Backend Microservicios

Esta colección de Postman contiene todas las pruebas necesarias para validar el funcionamiento de los microservicios del backend.

## Archivos Incluidos

1. **`postman_collection.json`** - Colección principal con todas las pruebas
2. **`postman_environment.json`** - Variables de entorno configurables

## Instalación

### Importar en Postman

1. Abrir Postman
2. Hacer clic en "Import"
3. Seleccionar y arrastrar ambos archivos JSON
4. Confirmar la importación

### Configurar Environment

1. En Postman, ir a "Environments"
2. Seleccionar "Backend Microservices Environment"
3. Verificar que todas las variables estén configuradas correctamente

## Variables Disponibles

### URLs de Servicios
- `base_url`: http://localhost:8001 (User Service)
- `audit_url`: http://localhost:8003 (Audit Service)  
- `nit_url`: http://localhost:8002 (NIT Validation Service)

### Datos de Prueba - Usuarios
- `nombre_exitoso`: "Clínica Central"
- `email_exitoso`: "admin@clinicacentral.org"
- `email_duplicado`: "admin@clinicacentral.org" (para pruebas de duplicados)
- `nombre_test`: "Hospital Test"
- `email_test`: "test@hospitaltest.com"
- `email_invalido`: "email-sin-formato-valido"

### Datos de Prueba - NITs
- `nit_valido`: "901234567" (existe en BD, formato string)
- `nit_invalido`: "999999999" (no existe en BD, formato string)

### Datos de Prueba - Passwords
- `password_valido`: "S3gura!2025" (cumple complejidad)
- `password_debil`: "123" (no cumple complejidad)

### Datos de Prueba - Auditoría
- `audit_event`: "user_register"
- `audit_nombre`: "Usuario de Prueba"
- `audit_email`: "audit@test.com"
- `audit_nit`: "123456789"
- `audit_outcome_success`: "success"
- `audit_outcome_fail`: "fail"
- `audit_action`: "email"

## Estructura de Pruebas

### User Service
1. **Registrar Usuario - Prueba Exitosa** (200)
2. **Registrar Usuario - NIT Inválido** (404)
3. **Registrar Usuario - Email Duplicado** (409)
4. **Registrar Usuario - Password Débil** (422)
5. **Registrar Usuario - Datos Inválidos** (400)
6. **Health Check User Service** (200)

### Audit Service
1. **Registrar Evento - Registro Exitoso** (201)
2. **Registrar Evento - Registro Fallido** (201)
3. **Health Check Audit Service** (200)

### NIT Validation Service
1. **Validar NIT Existente** (200)
2. **Validar NIT No Existente** (404)
3. **Health Check NIT Service** (200)

## Casos de Prueba Específicos

### Registro de Usuario Exitoso
```json
{
  "nombre": "{{nombre_exitoso}}",
  "email": "{{email_exitoso}}",
  "nit": "{{nit_valido}}",
  "password": "{{password_valido}}"
}
```
**Respuesta esperada**: 200 OK con JWT token

### Registro con NIT Inválido
```json
{
  "nombre": "{{nombre_test}}",
  "email": "{{email_test}}",
  "nit": "{{nit_invalido}}",
  "password": "{{password_valido}}"
}
```
**Respuesta esperada**: 404 Not Found

### Registro con Email Duplicado
```json
{
  "nombre": "{{nombre_exitoso}}",
  "email": "{{email_duplicado}}",
  "nit": "{{nit_valido}}",
  "password": "{{password_valido}}"
}
```
**Respuesta esperada**: 409 Conflict

### Registro con Password Débil
```json
{
  "nombre": "{{nombre_test}}",
  "email": "{{email_test}}",
  "nit": "{{nit_valido}}",
  "password": "{{password_debil}}"
}
```
**Respuesta esperada**: 422 Unprocessable Entity

## Variables Dinámicas

La colección utiliza variables dinámicas de Postman:
- `{{$isoTimestamp}}`: Genera timestamp automático
- `{{$guid}}`: Genera UUID automático para auditoría

## Ejecución de Pruebas

### Orden Recomendado
1. Verificar Health Checks de todos los servicios
2. Ejecutar prueba de NIT válido
3. Ejecutar registro exitoso
4. Ejecutar pruebas de errores (NIT inválido, email duplicado, etc.)
5. Verificar eventos de auditoría

### Pruebas Automáticas
Cada request incluye tests automáticos que verifican:
- Tiempo de respuesta < 2000ms
- Content-Type header presente
- Códigos de estado esperados

## Personalización

Para personalizar las variables:
1. Ir a Environment en Postman
2. Modificar los valores según tu entorno
3. Guardar cambios

### URLs Personalizadas
Si tus servicios corren en otros puertos o hosts:
```
base_url: http://tu-host:puerto-user-service
audit_url: http://tu-host:puerto-audit-service
nit_url: http://tu-host:puerto-nit-service
```

### Datos de Prueba Personalizados
Puedes modificar cualquier variable de datos de prueba según tus necesidades específicas.

## Troubleshooting

### Error de Conexión
- Verificar que todos los servicios estén ejecutándose
- Comprobar los puertos en las variables de entorno
- Revisar la configuración de Docker Compose

### Errores de Validación
- Verificar que los datos de prueba estén bien formateados
- Comprobar que el NIT válido existe en la base de datos
- Asegurar que el password cumple la política de complejidad

### Problemas de Base de Datos
- Verificar que las tablas estén creadas correctamente
- Comprobar que hay datos de muestra en `instituciones_asociadas`
- Revisar permisos de base de datos

## Soporte

Para problemas o preguntas sobre la colección, revisar:
1. Logs de los microservicios
2. Estado de la base de datos
3. Configuración de red/puertos