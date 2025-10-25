# Flujo de Trabajo del Equipo - Despliegues Monorepo

Guía rápida para el equipo sobre cómo trabajar con el sistema de despliegue monorepo.

## 🚀 Cuando Haces Cambios a un Servicio

### 1. Actualiza la Versión Manualmente

Edita el archivo `main.py` del servicio y actualiza la versión:

```python
# Ejemplo: user-service/main.py
app = FastAPI(
    title="User Service",
    version="2.2.0"  # ← Cambia esto
)
```

**Cuándo actualizar:**
- **Patch (2.1.1):** Corrección de bugs
- **Minor (2.2.0):** Nuevas funcionalidades
- **Major (3.0.0):** Cambios que rompen compatibilidad

### 2. Crea un PR a main o release

```bash
git add user-service/
git commit -m "feat: agregar nuevo endpoint"
git push origin feature/mi-funcionalidad
```

Luego crea un PR hacia la rama `main` o `release`.

### 3. Validación del PR (Automática)

GitHub Actions verificará:
- ✅ ¿Cambiaste código en un servicio?
- ✅ ¿Actualizaste la versión de ese servicio?

**Si olvidaste actualizar la versión:**
- ❌ El PR falla
- 🤖 El bot comenta en el PR con instrucciones
- 🚫 No se puede hacer merge del PR

**Cómo arreglarlo:**
```python
# Actualiza la versión en main.py
version="2.2.0"  # ← Incrementa esto

# Haz push del cambio
git add user-service/main.py
git commit -m "chore: incrementar versión a 2.2.0"
git push
```

### 4. Hacer Merge del PR

Una vez que el PR esté aprobado y todos los checks pasen:
- Haz merge a `main` o `release`
- **El despliegue automático ocurre:**
  - Se crea tag de Git: `user-service-v2.2.0`
  - Se construye imagen Docker
  - Se sube a AWS ECR
  - Se despliega a AWS ECS

## ❌ Qué NO Hacer

```python
# ❌ NO: Cambiar código sin actualizar la versión
# Esto hará que el PR falle

# Archivo: user-service/routes/users.py
def nuevo_endpoint():  # Código nuevo agregado
    pass

# Archivo: user-service/main.py
version="2.1.0"  # ← ¡Versión antigua! El PR fallará
```

## ✅ Qué SÍ Hacer

```python
# ✅ SÍ: Cambiar código Y actualizar versión

# Archivo: user-service/routes/users.py
def nuevo_endpoint():  # Código nuevo agregado
    pass

# Archivo: user-service/main.py
version="2.2.0"  # ← ¡Actualizada! El PR pasará
```

## 🔄 Cambios en Múltiples Servicios

Si cambias varios servicios en un PR:

```python
# user-service/main.py
version="2.2.0"  # ← Actualiza este

# auth-service/main.py
version="1.6.0"  # ← Y actualiza este
```

Al hacer merge:
- Crea 2 tags: `user-service-v2.2.0`, `auth-service-v1.6.0`
- Despliega ambos servicios en paralelo

## 📋 Checklist Rápido

Antes de crear un PR:

- [ ] ¿Cambiaste código en un servicio?
- [ ] ¿Actualizaste la versión en el `main.py` de ese servicio?
- [ ] ¿La versión sigue semver (X.Y.Z)?
- [ ] ¿El mensaje de commit sigue la convención?

## 🛠️ Opcional: Script de Ayuda

Hay un script de ayuda si quieres verificar versiones:

```bash
# Ver todas las versiones de servicios
./scripts/version-manager.sh list

# Ver tags de un servicio
./scripts/version-manager.sh list-tags user-service
```

**Pero no tienes que usarlo.** Simplemente edita `main.py` manualmente.

## 🐛 Solución de Problemas

**P: El check del PR falló, ¿cómo lo arreglo?**

R: Actualiza la versión en `main.py` y haz push:
```bash
# Edita la versión en main.py
vim user-service/main.py  # Cambia version="2.2.0"

# Commit y push
git add user-service/main.py
git commit -m "chore: incrementar versión"
git push
```

**P: Solo cambié un README, ¿necesito actualizar la versión?**

R: ¡No! El check solo revisa archivos de código. README, docs, tests (si están en directorio separado) no requieren actualización de versión.

**P: ¿Qué pasa si olvido actualizar la versión antes del merge?**

R: ¡No puedes hacer merge! El check del PR es obligatorio y bloqueará el merge hasta que actualices la versión.

**P: ¿Puedo desplegar sin hacer merge a main?**

R: Sí, usa despliegue manual con un tag existente:
```bash
gh workflow run deploy-by-tag.yml \
  -f tag=user-service-v2.1.0 \
  -f environment=production
```

## 📊 Resumen del Flujo de Trabajo

```
Desarrollador hace cambios
   ↓
Actualiza versión en main.py
   ↓
Crea PR a main/release
   ↓
GitHub Actions valida actualización de versión
   ↓
✅ Pasa → Se puede hacer merge
❌ Falla → Debe actualizar versión
   ↓
PR merged a main/release
   ↓
Despliegue automático:
  • Tag de Git creado
  • Build de Docker
  • Push a ECR
  • Deploy a ECS
```

## 🎯 Puntos Clave

1. **Siempre actualiza la versión** al cambiar código de un servicio
2. **La validación del PR es automática** - no necesitas hacer nada
3. **El script es opcional** - actualizar versiones manualmente está bien
4. **El despliegue es automático** - ocurre al hacer merge a main/release
5. **Los tags se crean automáticamente** - visibles en GitHub

---

**¿Preguntas?** Revisa `GUIA_DESPLIEGUE.md` para documentación completa.
