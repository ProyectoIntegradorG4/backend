# Guía de Testing: Visualización de Evidencias

## Cambios Implementados

### Backend (visit-service)

1. **Pre-signed URLs de S3** (`app/routes/visits.py`)
   - Modificada función `_url_for()` para generar URLs pre-firmadas con validez de 24 horas
   - URLs seguras que permiten acceso temporal a objetos privados de S3

2. **Endpoint de Regeneración** (`app/routes/visits.py`)
   - Nuevo endpoint: `GET /api/v1/visits/{visit_id}/evidence/{evidence_id}/url`
   - Permite regenerar URLs expiradas sin necesidad de recargar toda la visita

### Mobile App (MediSupplyMovilApp)

1. **Reproductor de Video** (`presentation/visits/components/VideoPlayer.tsx`)
   - Componente nuevo con expo-av
   - Controles nativos de reproducción
   - Soporte para fullscreen
   - Manejo de errores de carga

2. **Actualización de VisitDetailScreen** (`app/(products-app)/(visits)/[visitId].tsx`)
   - Integración del VideoPlayer para videos
   - Visualizador de imágenes para fotos
   - Detección automática del tipo de evidencia

3. **Dependencias**
   - Agregado `expo-av@~16.0.5` en package.json

4. **API Client** (`core/visits/api/visitsApi.ts`)
   - Nueva función `regenerateEvidenceUrl()` para renovar URLs expiradas

## Pasos de Testing

### 1. Preparación del Backend

```bash
# 1. Navegar al directorio del servicio
cd backend/visit-service

# 2. Verificar variables de entorno (archivo .env o docker-compose.yml)
# Asegurar que están configuradas:
FILES_BACKEND=s3
S3_BUCKET=tu-bucket-name
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=tu-access-key
AWS_SECRET_ACCESS_KEY=tu-secret-key

# 3. Reiniciar el servicio para aplicar cambios
docker-compose restart visit-service
# O si está en desarrollo local:
# uvicorn main:app --reload --host 0.0.0.0 --port 8011
```

### 2. Preparación de la App Móvil

```bash
# 1. Navegar al directorio de la app
cd MediSupplyMovilApp

# 2. Instalar dependencias nuevas (expo-av)
npm install
# o
yarn install

# 3. Limpiar caché de Metro (recomendado)
npx expo start --clear

# 4. Iniciar la aplicación
npm run android
# o
npm run ios
```

### 3. Test 1: Visualización de Imágenes

**Objetivo:** Verificar que las imágenes se visualizan correctamente con URLs pre-firmadas

**Pasos:**
1. Abrir la app móvil y autenticarse
2. Navegar a una visita existente que tenga evidencias de tipo imagen
   - O crear una nueva visita y subir una imagen
3. En la pantalla de detalle de visita, verificar que:
   - ✅ Las thumbnails de las imágenes se cargan correctamente
   - ✅ Al tocar una imagen, se abre el modal fullscreen
   - ✅ La imagen se muestra en alta resolución
   - ✅ El botón de cerrar (X) funciona correctamente

**Verificación en Backend:**
```bash
# Inspeccionar logs del visit-service
docker logs -f visit-service

# Buscar líneas que indiquen generación de pre-signed URLs
# Ejemplo: "Generating presigned URL for key: visits/123/photo.jpg"
```

**Verificación de URL:**
Las URLs devueltas deben tener el formato:
```
https://tu-bucket.s3.amazonaws.com/visits/123/photo.jpg?AWSAccessKeyId=...&Signature=...&Expires=...
```

### 4. Test 2: Reproducción de Videos

**Objetivo:** Verificar que los videos se reproducen correctamente

**Pasos:**
1. En la pantalla de detalle de visita
2. Subir o seleccionar una evidencia de tipo video
3. Tocar el card del video (con ícono de cámara)
4. Verificar que:
   - ✅ Se abre el modal del VideoPlayer
   - ✅ El video comienza a cargar (indicador de carga)
   - ✅ Los controles nativos aparecen
   - ✅ El botón play/pause funciona
   - ✅ Se puede reproducir el video completo
   - ✅ El botón de cerrar (X) funciona
   - ✅ La barra de progreso se muestra correctamente

**Notas:**
- Los videos pueden tardar unos segundos en cargar dependiendo del tamaño
- Si hay error de carga, el reproductor mostrará un mensaje de error

### 5. Test 3: Subida de Evidencias

**Objetivo:** Verificar el flujo completo de subida y visualización

**Pasos:**
1. Crear una nueva visita o abrir una existente
2. Tocar "Agregar Evidencia"
3. Subir una imagen:
   - Tomar foto con cámara o seleccionar de galería
   - Agregar comentario obligatorio
   - Tocar "Subir"
   - ✅ Verificar que la imagen aparece en la lista de evidencias
   - ✅ Tocar la imagen para visualizarla
4. Subir un video:
   - Grabar video o seleccionar de galería
   - Agregar comentario obligatorio
   - Tocar "Subir"
   - ✅ Verificar que el video aparece en la lista
   - ✅ Tocar el video para reproducirlo

### 6. Test 4: Regeneración de URLs (Opcional)

**Objetivo:** Verificar que las URLs expiradas se pueden regenerar

**Escenario de prueba:**
Este test solo es relevante si se espera que los usuarios vean evidencias después de 24 horas.

**Método 1 - Modificar expiración temporalmente:**
```python
# En backend/visit-service/app/routes/visits.py
# Cambiar temporalmente el ExpiresIn a 60 segundos
def _url_for(*, key: str) -> str:
    if FILES_BACKEND == "s3":
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=60  # 60 segundos para testing
        )
        return url
```

**Pasos:**
1. Modificar el backend como se indica arriba
2. Reiniciar el servicio
3. Abrir una visita con evidencias
4. Esperar 60 segundos
5. Intentar visualizar una evidencia
6. La URL debería estar expirada (error 403 o similar)
7. La app podría implementar auto-refresh llamando a `regenerateEvidenceUrl()`

### 7. Test 5: Compatibilidad de Plataformas

**Android:**
- ✅ Imágenes se cargan correctamente
- ✅ Videos se reproducen con controles nativos
- ✅ No hay errores de permisos de cámara/galería

**iOS:**
- ✅ Imágenes se cargan correctamente
- ✅ Videos se reproducen con controles nativos
- ✅ No hay errores de permisos de cámara/galería

## Troubleshooting

### Problema: Las imágenes no se cargan

**Posibles causas:**
1. Backend no genera pre-signed URLs correctamente
2. Configuración de S3 incorrecta
3. Permisos de bucket S3 no permiten GetObject

**Solución:**
```bash
# Verificar logs del backend
docker logs visit-service | grep "presigned"

# Verificar que boto3 está instalado
pip show boto3

# Verificar variables de entorno
echo $FILES_BACKEND
echo $S3_BUCKET
```

### Problema: Los videos no se reproducen

**Posibles causas:**
1. expo-av no está instalado correctamente
2. Formato de video no soportado
3. URL expiró

**Solución:**
```bash
# Reinstalar expo-av
cd MediSupplyMovilApp
npm install expo-av@~16.0.5

# Limpiar caché
npx expo start --clear

# Verificar formato de video (debe ser MP4 H.264)
```

### Problema: Error 403 Forbidden al acceder a S3

**Posibles causas:**
1. URL pre-firmada expiró
2. Configuración de CORS en S3 incorrecta
3. Permisos de IAM insuficientes

**Solución:**
```json
// Configuración de CORS recomendada para el bucket S3
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

## Validación de Calidad

### Checklist de Completitud

**Backend:**
- [x] Pre-signed URLs generadas correctamente
- [x] Expiración configurada a 24 horas
- [x] Endpoint de regeneración implementado
- [x] Sin errores de linting
- [x] Compatible con almacenamiento local y S3

**Mobile:**
- [x] VideoPlayer implementado con expo-av
- [x] Integración en VisitDetailScreen
- [x] Manejo correcto de imágenes y videos
- [x] Estados de carga y error manejados
- [x] expo-av agregado a package.json
- [x] Sin errores de TypeScript

### Performance

**Métricas esperadas:**
- Tiempo de carga de imagen: < 2 segundos
- Tiempo de inicio de video: < 3 segundos
- Tamaño máximo de archivo: 15MB
- URLs válidas por: 24 horas

## Conclusión

Después de completar todos los tests, las evidencias deberían:
1. ✅ Cargarse correctamente desde S3 con URLs pre-firmadas
2. ✅ Mostrarse en thumbnails en la lista de evidencias
3. ✅ Visualizarse en fullscreen (imágenes)
4. ✅ Reproducirse con controles nativos (videos)
5. ✅ Funcionar en Android e iOS
6. ✅ Manejar errores de carga apropiadamente

## Próximos Pasos (Opcional)

1. **Caché de URLs:** Implementar caché local para reducir llamadas al backend
2. **Renovación automática:** Auto-regenerar URLs cuando expiren
3. **Indicadores de progreso:** Mostrar progreso de carga de videos grandes
4. **Thumbnails de video:** Generar y mostrar thumbnails de videos en lugar de íconos
5. **Zoom en imágenes:** Permitir zoom/pan en el visualizador de imágenes

