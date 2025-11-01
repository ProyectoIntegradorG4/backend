# Guía de Despliegue - Patrón Monorepo

Esta guía explica cómo desplegar servicios en este monorepo usando el sistema automatizado de etiquetado y despliegue.

## Inicio Rápido

### Desplegando Cambios Automáticamente

1. **Actualiza la versión del servicio manualmente:**
   Edita el archivo `main.py` del servicio:
   ```python
   app = FastAPI(
       title="User Service",
       version="2.2.0"  # ← Actualiza esto
   )
   ```

2. **Crea un PR a main/release:**
   ```bash
   git add user-service/
   git commit -m "feat: agregar nueva funcionalidad"
   git push origin feature/mi-funcionalidad
   # Crear PR hacia main o release
   ```

3. **Validación de versión:**
   - El PR **automáticamente valida** que la versión fue actualizada
   - Si cambiaste código pero no actualizaste versión → **PR falla** ❌
   - Arréglalo actualizando versión en `main.py` → **PR pasa** ✅

4. **Proceso automático:**
   - ✅ GitHub Actions detecta cambios
   - ✅ Crea tag: `user-service-v2.2.0`
   - ✅ Construye imagen Docker
   - ✅ Sube a ECR
   - ✅ Despliega a AWS ECS
   - ✅ Espera que el servicio se estabilice

## Estructura del Monorepo

```
backend/
├── user-service/           # Servicio independiente
│   ├── main.py            # Contiene version="2.1.0"
│   └── ...
├── auth-service/           # Servicio independiente
│   ├── main.py            # Contiene version="1.5.0"
│   └── ...
├── nit-validation-service/ # Servicio independiente
└── audit-service/          # Servicio independiente
```

**Cada servicio:**
- Tiene su propia versión en `main.py`
- Obtiene su propio tag de Git cuando cambia
- Se despliega independientemente

## Estrategia de Etiquetado

### Formato de Tags
```
<nombre-servicio>-v<semver>
```

**Ejemplos:**
- `user-service-v2.1.0`
- `auth-service-v1.5.0`
- `nit-validation-service-v1.0.3`
- `audit-service-v2.0.0`

### Cuándo se Crean los Tags

Los tags se crean **automáticamente** cuando:
1. Haces merge de un PR a rama `main` o `release`
2. El directorio del servicio tiene cambios
3. El servicio tiene una versión válida en `main.py`

**Ejemplo de PR:**
```
PR #123: "Agregar funcionalidad de perfil de usuario"
Cambios:
  - user-service/routes/profile.py (archivo nuevo)
  - user-service/main.py (versión actualizada a 2.2.0)

Al hacer merge a main:
  → Tag creado: user-service-v2.2.0
  → Despliegue disparado solo para user-service
  → Otros servicios no se tocan
```

## Gestión de Versiones

### Actualización Manual de Versiones (Requerido)

**Todo el equipo actualiza versiones manualmente** editando `main.py`:

```python
# user-service/main.py
app = FastAPI(
    title="User Service",
    version="2.2.0"  # ← Actualiza esto al hacer cambios
)
```

**Validación del PR (Automática):**
- Cuando creas un PR a `main` o `release`
- GitHub Actions verifica si actualizaste la versión
- **Falla si:** El código cambió pero la versión no
- **Pasa si:** La versión fue actualizada

### Versionado Semántico

Sigue versionado semántico (semver):

- **Major (X.0.0):** Cambios que rompen compatibilidad
  - Cambios en esquema de base de datos
  - Cambios en contrato de API
  - Endpoints eliminados

- **Minor (x.Y.0):** Nuevas funcionalidades (compatible hacia atrás)
  - Nuevos endpoints
  - Nuevos parámetros opcionales
  - Nueva funcionalidad

- **Patch (x.y.Z):** Corrección de bugs (compatible hacia atrás)
  - Correcciones de seguridad
  - Corrección de bugs
  - Mejoras de rendimiento

**Ejemplo:**
```python
# Corrección de bug
version="2.1.1"

# Nueva funcionalidad
version="2.2.0"

# Cambio que rompe compatibilidad
version="3.0.0"
```

## Workflows de GitHub Actions

### 1. validate-version-bump.yml (Validación de PR)

**Se dispara:** En PRs a `main` o `release`

**Proceso:**
1. Detecta qué servicios tienen cambios de código
2. Verifica si la versión fue actualizada para esos servicios
3. **Falla el PR** si la versión no se actualizó
4. Comenta automáticamente en el PR con instrucciones

**No despliega** - solo valida el código

### 2. tag-and-deploy.yml (Despliegue Automático)

**Se dispara:** Push a `main` o `release`

**Proceso:**
1. Detecta servicios modificados (compara con commit anterior)
2. Extrae versión del `main.py` de cada servicio
3. Crea tag de Git para cada servicio modificado
4. Construye imágenes Docker con tag de versión
5. Sube a ECR
6. Actualiza servicio ECS con nueva definición de tarea
7. Espera que el despliegue se estabilice

**Salidas:**
- Tags de Git visibles en GitHub
- Servicio desplegado en AWS ECS
- Logs de CloudWatch en `/ecs/<nombre-servicio>`

### 3. deploy-by-tag.yml (Despliegue Manual)

**Se dispara:** Disparador manual de workflow

**Proceso:**
1. Valida formato del tag
2. Hace checkout del tag específico
3. Verifica que la versión coincida con el tag
4. Construye imagen Docker con esa versión
5. Despliega al ambiente especificado (prod/staging)

**Casos de uso:**
- Rollback a versión anterior
- Despliegue a ambiente de staging
- Desplegar versión específica sin nuevo commit

## Despliegue Manual por Tag

Despliega una versión etiquetada específica manualmente:

**Vía GitHub UI:**
1. Ve a Actions → "Deploy Service by Tag (Manual)"
2. Clic en "Run workflow"
3. Ingresa tag: `user-service-v2.1.0`
4. Selecciona ambiente: production
5. Clic en Run

**Vía GitHub CLI:**
```bash
# Desplegar tag específico a producción
gh workflow run deploy-by-tag.yml \
  -f tag=user-service-v2.1.0 \
  -f environment=production

# Desplegar a staging
gh workflow run deploy-by-tag.yml \
  -f tag=auth-service-v1.5.0 \
  -f environment=staging
```

## Despliegues Multi-Servicio

### Escenario: Actualizar Múltiples Servicios

```bash
# Estás trabajando en una funcionalidad que toca 2 servicios

# 1. Actualiza ambas versiones manualmente
# user-service/main.py → version="2.2.0"
# auth-service/main.py → version="1.6.0"

# 2. Haz tus cambios de código
# ... edita archivos ...

# 3. Commit todo
git add user-service/ auth-service/
git commit -m "feat: agregar soporte OAuth a servicios de usuario y auth"
git push origin main

# 4. GitHub Actions:
#    - Creará 2 tags:
#      - user-service-v2.2.0
#      - auth-service-v1.6.0
#    - Desplegará ambos servicios en paralelo
```

## Estrategia de Rollback

### Opción 1: Desplegar Tag Anterior

```bash
# Listar tags recientes
git tag --list "user-service-*" --sort=-v:refname

# Desplegar versión anterior
gh workflow run deploy-by-tag.yml \
  -f tag=user-service-v2.1.0 \
  -f environment=production
```

### Opción 2: Revertir y Redesplegar

```bash
# Revertir el commit
git revert <commit-hash>

# La versión permanece igual (o puedes incrementar patch)
git push origin main

# GitHub Actions redespliega con código revertido
```

## Solución de Problemas

### Tag Ya Existe

```
⚠️ Tag user-service-v2.1.0 ya existe, saltando
```

**Solución:** Incrementa a una nueva versión
```python
version="2.1.1"
```

### No se Detectaron Cambios

```
ℹ️ No hay servicios para etiquetar
```

**Solución:** Asegúrate de tener cambios en directorio del servicio
```bash
# Verifica qué cambió
git diff origin/main HEAD
```

### El Servicio No se Desplegó

1. **Revisa el workflow:** Ve a pestaña Actions, revisa logs
2. **Revisa la versión:** Asegura que versión en `main.py` sea válida
3. **Revisa ECR:** Verifica que la imagen se subió
4. **Revisa ECS:** Revisa eventos del servicio en consola AWS

## Mejores Prácticas

### 1. Siempre Actualiza Versión Antes del Despliegue

```python
# ✅ Bueno
# Edita user-service/main.py
version="2.2.0"

# Haz cambios
# ...

# Commit y push
git push origin main

# ❌ Malo
# Haz cambios sin actualizar versión
# (El PR fallará)
```

### 2. Usa Commits Convencionales

```bash
# Incrementos de versión
git commit -m "chore: incrementar user-service a v2.2.0"

# Funcionalidades
git commit -m "feat: agregar endpoints de perfil de usuario"

# Corrección de bugs
git commit -m "fix: resolver problema de validación de contraseña"

# Cambios que rompen compatibilidad
git commit -m "feat!: migrar a nueva API de autenticación"
```

### 3. Revisa Cambios Antes del Merge

```bash
# Verifica qué será desplegado
git diff main..tu-rama user-service/

# Valida versiones
grep -r 'version=' */main.py
```

## Monitoreo de Despliegues

### GitHub Actions
- Ve a repositorio → pestaña Actions
- Ver ejecuciones de workflows
- Revisar logs de cada servicio

### AWS ECS
```bash
# Revisar estado del servicio
aws ecs describe-services \
  --cluster microservices-cluster \
  --services user-service

# Ver logs
aws logs tail /ecs/user-service --follow
```

## Preguntas Frecuentes

**P: ¿Puedo desplegar sin crear un tag?**
R: No. El sistema requiere tags para trazabilidad y capacidad de rollback.

**P: ¿Qué pasa si necesito desplegar la misma versión otra vez?**
R: Incrementa a una versión patch (ej. 2.1.0 → 2.1.1) o usa workflow manual con tag existente.

**P: ¿Puedo desplegar a múltiples ambientes simultáneamente?**
R: Sí, ejecuta el workflow manual múltiples veces con diferentes ambientes.

**P: ¿Qué pasa si el despliegue falla?**
R: ECS mantiene ejecutando la tarea anterior. Revisa logs y redespliega después de arreglar.

---

**Más información:** Ver `FLUJO_EQUIPO.md` para guía rápida del equipo.
