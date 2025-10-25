# Despliegue Simple de Docker en AWS

Esta guía te muestra cómo desplegar tus microservicios en AWS usando Docker y GitHub Actions - **¡sin gestión compleja de infraestructura requerida!**

## 🚀 Inicio Rápido (5 minutos)

### 1. Ejecutar Script de Configuración
```bash
chmod +x aws-deployment/setup.sh
./aws-deployment/setup.sh
```

### 2. Agregar Secretos de GitHub
Ve a tu repositorio de GitHub → Settings → Secrets and variables → Actions, y agrega:

```
AWS_ACCESS_KEY_ID: Tu AWS Access Key ID
AWS_SECRET_ACCESS_KEY: Tu AWS Secret Access Key
RDS_ENDPOINT: [Obtener desde AWS Console o CLI]
REDIS_ENDPOINT: [Obtener desde AWS Console o CLI]
POSTGRES_PASSWORD: Microservices123!
JWT_SECRET_KEY: your-super-secret-jwt-key-change-in-production-2024
```

### 3. Inicializar Base de Datos
```bash
# Obtener endpoint de RDS
aws rds describe-db-instances --db-instance-identifier microservices-db --query 'DBInstances[0].Endpoint.Address' --output text

# Conectar e inicializar
psql -h [RDS_ENDPOINT] -U postgres -d postgres -f 001-init.sql
```

### 4. ¡Desplegar!
```bash
git add .
git commit -m "Desplegar microservicios en AWS"
git push origin main
```

**¡Eso es todo!** Tus microservicios se desplegarán automáticamente en AWS ECS.

## 📁 Lo Que Se Crea

### Recursos de AWS:
- **ECS Fargate Cluster** - Ejecuta tus contenedores
- **ECR Repositories** - Almacena tus imágenes Docker
- **RDS PostgreSQL** - Base de datos para todos los servicios
- **ElastiCache Redis** - Capa de caché
- **CloudWatch Logs** - Registro de aplicaciones

### GitHub Actions:
- **`.github/workflows/ci.yml`** - Ejecuta pruebas en cada push/PR
- **`.github/workflows/deploy.yml`** - Despliega en AWS al hacer push a main

### Archivos Docker:
- **`docker-compose.aws.yml`** - Versión optimizada para AWS de tu docker-compose
- **Tus Dockerfiles existentes** - ¡No se necesitan cambios!

## 🔄 Cómo Funciona

1. **Push a rama main** → GitHub Actions se activa
2. **Detección inteligente** → Compara versiones en `main.py` con las desplegadas
3. **Construir imágenes Docker** → Solo para servicios modificados
4. **Subir a ECR** → Con versión específica y `latest`
5. **Desplegar en ECS** → Solo servicios que cambiaron
6. **Verificaciones de salud** → Verificar que los servicios estén ejecutándose

## 🎯 Sistema de Despliegue Inteligente

### **Detección Automática de Cambios**
El sistema detecta automáticamente qué servicios necesitan despliegue comparando:
- **Versión actual** en `main.py` de cada servicio
- **Versión desplegada** en ECR (última imagen)

### **Solo Despliega Servicios Modificados**
- ✅ **Servicio nuevo** → Primera vez desplegando
- ✅ **Versión actualizada** → Cambio detectado en `main.py`
- ❌ **Sin cambios** → No se despliega

### **Etiquetado Inteligente de Docker**
- **Imagen con versión**: `service-name:1.2.0`
- **Imagen latest**: `service-name:latest`
- **Historial completo** de versiones en ECR

## 🚀 Actualizar Versiones de Servicios

### **Método Automático (Recomendado)**
```bash
# Usar el script de actualización
./aws-deployment/update-version.sh user-service 2.1.0

# Hacer commit y push
git add user-service/main.py
git commit -m "Actualizar user-service a versión 2.1.0"
git push origin main
```

### **Método Manual**
```bash
# 1. Editar main.py del servicio
vim user-service/main.py

# 2. Cambiar la versión
version="2.1.0"  # En lugar de "2.0.0"

# 3. Commit y push
git add user-service/main.py
git commit -m "Actualizar user-service a versión 2.1.0"
git push origin main
```

### **Probar Detección Localmente**
```bash
# Ver qué servicios necesitan despliegue
./aws-deployment/detect-changes.sh

# Con información detallada
./aws-deployment/detect-changes.sh --verbose
```

## 🎯 Servicios Desplegados

| Servicio | Puerto | Verificación de Salud | Base de Datos | Versión Actual |
|----------|--------|----------------------|---------------|----------------|
| **nit-validation-service** | 8002 | `/api/v1/health` | `nit_db` | 1.0.0 |
| **user-service** | 8001 | `/health` | `user_db` | 2.0.0 |
| **audit-service** | 8003 | `/health` | `audit_db` | 1.0.0 |
| **auth-service** | 8004 | `/health` | `user_db` | 1.0.0 |

## 💰 Estimación de Costos

**Costos mensuales (us-east-1):**
- ECS Fargate (4 servicios): ~$50-80
- RDS PostgreSQL (db.t3.micro): ~$15-20
- ElastiCache Redis (cache.t3.micro): ~$15-20
- CloudWatch Logs: ~$5-10
- **Total: ~$85-130/mes**

## 🔧 Solución de Problemas

### ¿Servicio No Inicia?
```bash
# Verificar estado del servicio ECS
aws ecs describe-services --cluster microservices-cluster --services nit-validation-service

# Ver logs
aws logs tail /ecs/nit-validation-service --follow
```

### ¿Problemas de Conexión a Base de Datos?
```bash
# Verificar estado de RDS
aws rds describe-db-instances --db-instance-identifier microservices-db

# Probar conexión
psql -h [RDS_ENDPOINT] -U postgres -d postgres -c "SELECT 1;"
```

### ¿Fallan las Verificaciones de Salud?
- Verificar que las reglas del security group permitan tráfico
- Verificar que los servicios estén escuchando en los puertos correctos
- Revisar logs de CloudWatch para errores

## 🚀 Escalado

### Auto Escalado
ECS escala automáticamente basado en uso de CPU/memoria.

### Escalado Manual
```bash
# Escalar un servicio
aws ecs update-service \
  --cluster microservices-cluster \
  --service nit-validation-service \
  --desired-count 3
```

## 🔒 Seguridad

### Mejores Prácticas:
- ✅ **Roles IAM** en lugar de access keys cuando sea posible
- ✅ **Security groups de VPC** restringen acceso de red
- ✅ **RDS y ElastiCache encriptados**
- ✅ **Secretos en GitHub** (no en código)
- ✅ **Actualizaciones de seguridad regulares** vía GitHub Actions

### Recomendaciones para Producción:
- Usar **AWS Secrets Manager** para datos sensibles
- Habilitar **AWS WAF** para protección web
- Configurar **AWS Config** para cumplimiento
- Usar **AWS GuardDuty** para detección de amenazas

## 📊 Monitoreo

### Métricas de CloudWatch:
- Uso de CPU/Memoria por servicio
- Conteo de requests y latencia
- Tasas de error y estado de health checks

### Logs:
- Logs de aplicación: `/ecs/[nombre-servicio]`
- Logs de servicio ECS: Disponibles en consola ECS

## 🎉 ¡Éxito!

Tus microservicios ahora están ejecutándose en AWS con:
- ✅ **Despliegues automáticos** en cambios de código
- ✅ **Monitoreo de salud** y recuperación automática
- ✅ **Infraestructura escalable** que crece con tus necesidades
- ✅ **Solución rentable** optimizada para contenedores

**¡No se requiere gestión compleja de infraestructura!** 🚀