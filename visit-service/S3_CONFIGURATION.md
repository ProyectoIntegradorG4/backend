# Configuración de Amazon S3 para visit-service

## 📋 Resumen de la Arquitectura

### Flujo Backend-Managed (Implementación Actual)

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  App Móvil  │────────>│visit-service │────────>│  Amazon S3  │
│             │  Upload │   (Backend)  │  Upload │   (Bucket)  │
└─────────────┘         └──────────────┘         └─────────────┘
       │                        │                        │
       │                        │                        │
       │    Pre-signed URL      │    Generate URL        │
       │<───────────────────────│<───────────────────────│
       │                        │                        │
       │    Visualizar Archivo  │                        │
       │───────────────────────────────────────────────>│
                                                         │
```

### ✅ Ventajas de esta Implementación

1. **Control Total:** El backend valida archivos antes de subirlos
2. **Seguridad:** No se exponen credenciales de S3 al cliente
3. **Auditoría:** Todos los uploads pasan por el backend (logs completos)
4. **Simplicidad:** La app móvil solo necesita enviar FormData
5. **Validación:** Tipo de archivo, tamaño, permisos verificados en backend

## 🔧 Configuración de S3

### 1. Crear Bucket S3

```bash
# Nombre del bucket (debe ser único globalmente)
BUCKET_NAME="medisupply-visit-evidences"

# Región (cerca de tus usuarios)
AWS_REGION="us-east-1"
```

**Desde AWS Console:**
1. Ir a S3 → Create bucket
2. Nombre: `medisupply-visit-evidences`
3. Región: `us-east-1` (o la más cercana)
4. **Block Public Access:** MANTENER ACTIVADO ✅
   - Block all public access: ✅ YES
   - Los archivos serán privados, accesibles solo via pre-signed URLs

### 2. Configurar CORS en el Bucket

Las pre-signed URLs necesitan CORS configurado para que el móvil pueda visualizar:

**Desde AWS Console:**
1. Ir al bucket → Permissions → CORS
2. Agregar esta configuración:

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "HEAD"
        ],
        "AllowedOrigins": [
            "*"
        ],
        "ExposeHeaders": [
            "ETag",
            "x-amz-server-side-encryption",
            "x-amz-request-id",
            "x-amz-id-2"
        ],
        "MaxAgeSeconds": 3000
    }
]
```

**Nota:** En producción, cambiar `"AllowedOrigins": ["*"]` por tu dominio específico.

### 3. Crear Usuario IAM con Permisos

**Desde AWS Console:**
1. Ir a IAM → Users → Create user
2. Nombre: `medisupply-visit-service-user`
3. Attach policies directly → Create policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisitServiceS3Access",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::medisupply-visit-evidences",
                "arn:aws:s3:::medisupply-visit-evidences/*"
            ]
        }
    ]
}
```

4. Guardar policy como: `MediSupplyVisitServiceS3Policy`
5. Crear Access Key → Application running outside AWS
6. **GUARDAR:** Access Key ID y Secret Access Key

### 4. Configurar Variables de Entorno

**Archivo `.env` o Docker Compose:**

```bash
# === Configuración de Almacenamiento ===
FILES_BACKEND=s3                    # "s3" o "local"
MAX_UPLOAD_MB=15                    # Tamaño máximo de archivo (MB)

# === Configuración de S3 ===
S3_BUCKET=medisupply-visit-evidences
S3_PREFIX=visits                    # Prefijo para organizar archivos
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...          # Tu Access Key ID
AWS_SECRET_ACCESS_KEY=abc123...    # Tu Secret Access Key

# === URLs (NO necesario con S3) ===
# FILES_BASE_URL no se usa cuando FILES_BACKEND=s3
# Las URLs se generan automáticamente con pre-signed URLs
```

**Docker Compose Example:**

```yaml
services:
  visit-service:
    build: ./visit-service
    environment:
      # Database
      DB_HOST: visit-db
      DB_PORT: 5432
      DB_NAME: visit_db
      DB_USER: visit_user
      DB_PASSWORD: visit_password
      
      # Files & S3
      FILES_BACKEND: s3
      MAX_UPLOAD_MB: 15
      S3_BUCKET: medisupply-visit-evidences
      S3_PREFIX: visits
      AWS_REGION: us-east-1
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      
      # Auth
      JWT_SECRET: ${JWT_SECRET}
    ports:
      - "8011:8011"
```

## 🔐 Seguridad

### Permisos del Bucket

✅ **Configuración Recomendada:**
- Block all public access: **SÍ** ✅
- Object ownership: BucketOwnerEnforced
- Encryption: AES-256 (SSE-S3) o KMS

### Pre-signed URLs

La implementación actual genera URLs con:
- **Expiración:** 24 horas (86400 segundos)
- **Operación:** `get_object` (solo lectura)
- **Sin permisos adicionales:** No pueden subir, modificar o eliminar

```python
# backend/visit-service/app/routes/visits.py
def _url_for(*, key: str) -> str:
    if FILES_BACKEND == "s3":
        url = s3.generate_presigned_url(
            'get_object',  # Solo lectura
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=86400  # 24 horas
        )
        return url
```

## 📊 Organización de Archivos en S3

### Estructura del Bucket

```
medisupply-visit-evidences/
└── visits/                         # S3_PREFIX
    ├── 123/                        # visit_id
    │   ├── photo_1234567890.jpg
    │   ├── video_1234567891.mp4
    │   └── photo_1234567892.jpg
    ├── 124/
    │   ├── photo_1234567893.jpg
    │   └── video_1234567894.mp4
    └── 125/
        └── photo_1234567895.jpg
```

**Ventajas:**
- Fácil de buscar por visit_id
- Fácil de eliminar todas las evidencias de una visita
- Nombres únicos con timestamp

## 🔄 Flujos de Operación

### Flujo de Subida (Upload)

```
1. App Móvil prepara FormData
   ├── file: {uri, type, name}
   └── comment: "Evidencia de la visita"

2. App envía POST /visits/{visit_id}/evidence
   ├── Headers: Authorization, X-User-Id, X-User-Role
   └── Body: FormData (multipart/form-data)

3. Backend (visit-service)
   ├── Valida autenticación y permisos
   ├── Valida tamaño del archivo (< 15MB)
   ├── Valida tipo de archivo (image/* o video/*)
   ├── Lee el contenido del archivo
   ├── Sube a S3 usando boto3:
   │   └── s3.put_object(Bucket, Key, Body, ContentType)
   ├── Guarda metadata en DB (VisitEvidence)
   └── Retorna URL pre-firmada para visualización

4. App recibe respuesta
   └── {items: [{id, filename, url, ...}], count: 1}
```

### Flujo de Visualización (Download/View)

```
1. App solicita GET /api/v1/visits/{visit_id}

2. Backend (visit-service)
   ├── Consulta DB para obtener visita y evidencias
   ├── Para cada evidencia:
   │   └── Genera pre-signed URL (válida 24h)
   └── Retorna JSON con URLs

3. App recibe respuesta
   └── {id, evidences: [{id, url, ...}]}

4. App usa las URLs para mostrar contenido
   ├── Imágenes: <Image source={{uri: evidence.url}} />
   └── Videos: <Video source={{uri: evidence.url}} />

5. React Native descarga directamente desde S3
   └── Usando la pre-signed URL (sin pasar por backend)
```

### Flujo de Regeneración de URL (Opcional)

```
1. Si la URL expiró (> 24h)

2. App solicita GET /api/v1/visits/{visit_id}/evidence/{evidence_id}/url

3. Backend genera nueva pre-signed URL

4. App recibe {url: "https://...", expires_in_seconds: 86400}

5. App actualiza la URL y vuelve a intentar visualizar
```

## 🧪 Testing

### 1. Verificar Configuración de S3

```bash
# Test de conectividad con AWS CLI
aws s3 ls s3://medisupply-visit-evidences --region us-east-1

# Test de subida
echo "test" > test.txt
aws s3 cp test.txt s3://medisupply-visit-evidences/visits/test/test.txt

# Test de lectura
aws s3 cp s3://medisupply-visit-evidences/visits/test/test.txt -

# Limpiar
aws s3 rm s3://medisupply-visit-evidences/visits/test/test.txt
```

### 2. Verificar Backend

```bash
# Logs del servicio
docker logs -f visit-service

# Buscar inicialización de S3
# Debe mostrar: "S3 client initialized for bucket: medisupply-visit-evidences"
```

### 3. Test desde App Móvil

Ver archivo: `TESTING_EVIDENCE_DISPLAY.md`

## 🚨 Troubleshooting

### Error: "S3 client not initialized"

**Causa:** `FILES_BACKEND` no está configurado como "s3" o boto3 no está instalado.

**Solución:**
```bash
# Verificar variable de entorno
docker exec visit-service env | grep FILES_BACKEND

# Debe retornar: FILES_BACKEND=s3

# Verificar boto3
docker exec visit-service pip show boto3
```

### Error: "NoSuchBucket"

**Causa:** El bucket no existe o el nombre está mal.

**Solución:**
```bash
# Verificar que el bucket existe
aws s3 ls | grep medisupply-visit-evidences

# Verificar variable de entorno
docker exec visit-service env | grep S3_BUCKET
```

### Error: "AccessDenied" al subir

**Causa:** Credenciales incorrectas o sin permisos de `s3:PutObject`.

**Solución:**
1. Verificar Access Key y Secret Key
2. Verificar política IAM incluye `s3:PutObject`
3. Verificar región correcta

### Error: "403 Forbidden" al visualizar

**Causa:** URL pre-firmada expiró o CORS mal configurado.

**Solución:**
1. Si expiró (> 24h): Regenerar URL con endpoint de regeneración
2. Verificar configuración CORS del bucket
3. Verificar que el objeto existe en S3

### Error: "SignatureDoesNotMatch"

**Causa:** Reloj del servidor desincronizado o credenciales incorrectas.

**Solución:**
```bash
# Verificar hora del servidor
docker exec visit-service date

# Sincronizar reloj del host
sudo ntpdate -s time.nist.gov
```

## 📈 Optimizaciones

### 1. Lifecycle Policies (Opcional)

Para reducir costos, puedes configurar políticas de ciclo de vida:

```json
{
    "Rules": [
        {
            "Id": "MoveOldEvidencesToGlacier",
            "Status": "Enabled",
            "Prefix": "visits/",
            "Transitions": [
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ]
        }
    ]
}
```

### 2. CloudFront (Opcional)

Para mejorar velocidad de descarga global:
1. Crear distribución CloudFront
2. Origen: Tu bucket S3
3. Actualizar `_url_for()` para usar CloudFront URLs

### 3. Compresión de Imágenes (Futuro)

Considerar comprimir imágenes antes de subir:
- Usar Pillow o ImageMagick en el backend
- Reducir calidad a 80-85%
- Redimensionar a máximo 1920x1080

## 📚 Referencias

- [Boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Presigned URLs Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html)
- [S3 Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

## ✅ Checklist de Implementación

- [ ] Bucket S3 creado con Block Public Access activado
- [ ] Configuración CORS agregada al bucket
- [ ] Usuario IAM creado con política de permisos
- [ ] Access Key y Secret Key generados
- [ ] Variables de entorno configuradas en visit-service
- [ ] Backend reiniciado con nueva configuración
- [ ] Test de subida desde app móvil exitoso
- [ ] Test de visualización de imágenes exitoso
- [ ] Test de reproducción de videos exitoso
- [ ] Logs verificados sin errores
- [ ] Documentación compartida con el equipo

