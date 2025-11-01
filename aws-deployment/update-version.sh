#!/bin/bash

# Script de ejemplo para actualizar versiones y probar el sistema de despliegue inteligente

set -e

echo "🔧 Script de Ejemplo - Actualización de Versiones"
echo "================================================="

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [servicio] [nueva-versión]"
    echo ""
    echo "Ejemplos:"
    echo "  $0 user-service 2.1.0          # Actualizar user-service a versión 2.1.0"
    echo "  $0 auth-service 1.1.0          # Actualizar auth-service a versión 1.1.0"
    echo "  $0 nit-validation-service 1.2.0 # Actualizar nit-validation-service a versión 1.2.0"
    echo "  $0 audit-service 1.1.0         # Actualizar audit-service a versión 1.1.0"
    echo ""
    echo "Servicios disponibles:"
    echo "  - nit-validation-service"
    echo "  - user-service"
    echo "  - audit-service"
    echo "  - auth-service"
}

# Verificar argumentos
if [ $# -ne 2 ]; then
    echo "❌ Error: Se requieren exactamente 2 argumentos"
    show_help
    exit 1
fi

SERVICE=$1
NEW_VERSION=$2

# Verificar que el servicio existe
if [ ! -d "$SERVICE" ]; then
    echo "❌ Error: El servicio '$SERVICE' no existe"
    echo ""
    echo "Servicios disponibles:"
    ls -d */ | sed 's/\///g' | grep -E "(nit-validation-service|user-service|audit-service|auth-service)"
    exit 1
fi

# Verificar que main.py existe
if [ ! -f "$SERVICE/main.py" ]; then
    echo "❌ Error: No se encontró main.py en $SERVICE"
    exit 1
fi

# Obtener versión actual
CURRENT_VERSION=$(grep -o 'version="[^"]*"' "$SERVICE/main.py" | sed 's/version="\(.*\)"/\1/')

if [ -z "$CURRENT_VERSION" ]; then
    echo "❌ Error: No se pudo extraer la versión actual de $SERVICE/main.py"
    exit 1
fi

echo "📦 Servicio: $SERVICE"
echo "📋 Versión actual: $CURRENT_VERSION"
echo "🚀 Nueva versión: $NEW_VERSION"
echo ""

# Confirmar actualización
read -p "¿Confirmas la actualización? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Actualización cancelada"
    exit 1
fi

# Crear backup
echo "💾 Creando backup de $SERVICE/main.py..."
cp "$SERVICE/main.py" "$SERVICE/main.py.backup"

# Actualizar versión
echo "🔄 Actualizando versión en $SERVICE/main.py..."
sed -i.tmp "s/version=\"$CURRENT_VERSION\"/version=\"$NEW_VERSION\"/" "$SERVICE/main.py"
rm "$SERVICE/main.py.tmp"

# Verificar actualización
UPDATED_VERSION=$(grep -o 'version="[^"]*"' "$SERVICE/main.py" | sed 's/version="\(.*\)"/\1/')

if [ "$UPDATED_VERSION" = "$NEW_VERSION" ]; then
    echo "✅ Versión actualizada exitosamente: $CURRENT_VERSION → $NEW_VERSION"
else
    echo "❌ Error: La versión no se actualizó correctamente"
    echo "🔄 Restaurando backup..."
    mv "$SERVICE/main.py.backup" "$SERVICE/main.py"
    exit 1
fi

# Limpiar backup
rm "$SERVICE/main.py.backup"

echo ""
echo "🎉 ¡Actualización completada!"
echo ""
echo "Próximos pasos:"
echo "1. Haz commit de los cambios:"
echo "   git add $SERVICE/main.py"
echo "   git commit -m \"Actualizar $SERVICE a versión $NEW_VERSION\""
echo ""
echo "2. Haz push para activar el despliegue:"
echo "   git push origin main"
echo ""
echo "3. El sistema detectará automáticamente el cambio y desplegará solo $SERVICE"
echo ""
echo "💡 Para probar la detección localmente:"
echo "   ./aws-deployment/detect-changes.sh"
