# 🚀 Comandos CURL - Cliente Service (Simplificado - Sin Auth)

## ✅ Estado del Servicio
- **Puerto**: 8013
- **Base URL**: http://localhost:8013
- **Autenticación**: NO requerida
- **Total clientes**: 30 (10 Colombia, 8 Perú, 7 México, 5 Ecuador)

---

## 📋 Endpoint 1: Listar Mis Clientes

### Comando Base
```bash
curl http://localhost/api/v1/clientes/mis-clientes
```

**Respuesta**: Retorna los 30 clientes de todos los países

---

### Filtrar por País

```bash
# Colombia (10 clientes)
curl "http://localhost/api/v1/clientes/mis-clientes?pais=Colombia"

# Perú (8 clientes)
curl "http://localhost/api/v1/clientes/mis-clientes?pais=Peru"

# México (7 clientes)
curl "http://localhost/api/v1/clientes/mis-clientes?pais=Mexico"

# Ecuador (5 clientes)
curl "http://localhost/api/v1/clientes/mis-clientes?pais=Ecuador"
```

---

### Filtrar por Tipo de Institución

```bash
# Todos los Hospitales
curl "http://localhost/api/v1/clientes/mis-clientes?tipo_institucion=Hospital"

# Todas las Clínicas
curl "http://localhost/api/v1/clientes/mis-clientes?tipo_institucion=Clínica"

# Todas las IPS
curl "http://localhost/api/v1/clientes/mis-clientes?tipo_institucion=IPS"

# Todas las EPS
curl "http://localhost/api/v1/clientes/mis-clientes?tipo_institucion=EPS"

# Laboratorios Clínicos
curl "http://localhost/api/v1/clientes/mis-clientes?tipo_institucion=Laboratorio%20Clínico"

# Centros de Salud
curl "http://localhost/api/v1/clientes/mis-clientes?tipo_institucion=Centro%20de%20Salud"
```

---

### Combinar Filtros

```bash
# Hospitales de Colombia
curl "http://localhost/api/v1/clientes/mis-clientes?pais=Colombia&tipo_institucion=Hospital"

# Clínicas de Perú
curl "http://localhost/api/v1/clientes/mis-clientes?pais=Peru&tipo_institucion=Clínica"

# IPS de México
curl "http://localhost/api/v1/clientes/mis-clientes?pais=Mexico&tipo_institucion=IPS"
```

---

### Búsqueda por Texto

```bash
# Buscar "Lima"
curl "http://localhost/api/v1/clientes/mis-clientes?search=Lima"

# Buscar "Bogotá"
curl "http://localhost/api/v1/clientes/mis-clientes?search=Bogotá"

# Buscar "Hospital"
curl "http://localhost/api/v1/clientes/mis-clientes?search=Hospital"

# Buscar en Colombia "Medellín"
curl "http://localhost/api/v1/clientes/mis-clientes?pais=Colombia&search=Medellín"
```

---

### Paginación

```bash
# Primera página, 5 elementos
curl "http://localhost/api/v1/clientes/mis-clientes?page=1&limit=5"

# Segunda página, 5 elementos
curl "http://localhost/api/v1/clientes/mis-clientes?page=2&limit=5"

# Primera página, 10 elementos
curl "http://localhost/api/v1/clientes/mis-clientes?page=1&limit=10"

# Hospitales paginados (3 por página)
curl "http://localhost/api/v1/clientes/mis-clientes?tipo_institucion=Hospital&page=1&limit=3"
```

---

## 🔍 Endpoint 2: Detalle de Cliente

```bash
# Cliente ID 1 (Hospital San Juan - Colombia)
curl http://localhost/api/v1/clientes/1

# Cliente ID 5 (Centro de Salud Norte - Colombia)
curl http://localhost/api/v1/clientes/5

# Cliente ID 11 (Hospital Nacional Dos de Mayo - Perú)
curl http://localhost/api/v1/clientes/11

# Cliente ID 19 (Hospital Español de México - México)
curl http://localhost/api/v1/clientes/19

# Cliente ID 26 (Hospital Metropolitano - Ecuador)
curl http://localhost/api/v1/clientes/26
```

**Formato bonito** (Linux/Mac con jq):
```bash
curl -s http://localhost/api/v1/clientes/1 | jq
```

---

## 📚 Endpoint 3: Tipos de Institución

```bash
curl http://localhost/api/v1/clientes/tipos-institucion
```

**Respuesta**:
```json
{
  "tipos": [
    "Hospital",
    "Clínica",
    "IPS",
    "EPS",
    "Laboratorio Clínico",
    "Centro de Salud"
  ]
}
```

---

## 💚 Endpoint 4: Health Check

```bash
# Health check a través de API Gateway
curl http://localhost/health/cliente

# Health check directo al servicio
curl http://localhost:8013/health
```

**Respuesta**:
```json
{
  "status": "healthy",
  "service": "cliente-service",
  "version": "1.0.0"
}
```

---

## 📊 Estadísticas de Datos

### Por País
- 🇨🇴 **Colombia**: 10 clientes
- 🇵🇪 **Perú**: 8 clientes
- 🇲🇽 **México**: 7 clientes
- 🇪🇨 **Ecuador**: 5 clientes

### Por Tipo (Total)
- **Hospital**: 11
- **Clínica**: 6
- **IPS**: 4
- **Laboratorio Clínico**: 4
- **Centro de Salud**: 3
- **EPS**: 2

### Por Tipo en Colombia
- **Hospital**: 3
- **Clínica**: 2
- **IPS**: 2
- **Laboratorio Clínico**: 1
- **Centro de Salud**: 1
- **EPS**: 1

---

## 🎯 Ejemplos Prácticos

### Consulta 1: Hospitales de Colombia
```bash
curl "http://localhost:8013/api/v1/clientes/mis-clientes?pais=Colombia&tipo_institucion=Hospital"
```

**Resultado**: 3 hospitales
- Hospital San Juan (Bogotá)
- Hospital Infantil (Medellín)
- Hospital Universitario (Cali)

### Consulta 2: Clientes en Lima
```bash
curl "http://localhost/api/v1/clientes/mis-clientes?search=Lima"
```

**Resultado**: 5 clientes en Lima, Perú

### Consulta 3: Primera página de 5 clientes de México
```bash
curl "http://localhost:8013/api/v1/clientes/mis-clientes?pais=Mexico&page=1&limit=5"
```

**Resultado**: 5 de 7 clientes mexicanos

---

## 🔄 Reiniciar Servicio

Si necesitas reiniciar el servicio:

```powershell
cd C:\MISORepos\MediSupplyApp\backend
docker-compose restart cliente-service
```

---

## 📝 Notas

1. El servicio retorna **30 clientes** distribuidos en 4 países
2. Los filtros son **case-insensitive** para la búsqueda
3. La paginación tiene un **límite máximo de 100** elementos por página
4. Por defecto, solo retorna clientes **activos** (`activo=true`)
5. Si no se especifica país, retorna clientes de **todos los países**

---

## ✨ Ventajas

- ✅ **Sin autenticación**: Acceso inmediato sin JWT
- ✅ **Múltiples filtros**: Por país, tipo, búsqueda de texto
- ✅ **Paginación eficiente**: Control total del tamaño de respuesta
- ✅ **Respuesta rápida**: < 1 segundo por request
- ✅ **30 clientes de prueba**: Datos realistas de 4 países

---

¡El servicio está **100% funcional** y listo para usar! 🚀

