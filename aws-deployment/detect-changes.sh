#!/bin/bash

# Script para detectar servicios modificados basado en versiones
# Este script extrae las versiones de main.py y las compara con las desplegadas

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para extraer versión de main.py
extract_version() {
    local service_dir=$1
    local main_file="$service_dir/main.py"
    
    if [ ! -f "$main_file" ]; then
        echo "❌ No se encontró main.py en $service_dir"
        return 1
    fi
    
    # Extraer versión usando grep y sed
    local version=$(grep -o 'version="[^"]*"' "$main_file" | sed 's/version="\(.*\)"/\1/')
    
    if [ -z "$version" ]; then
        echo "❌ No se pudo extraer versión de $main_file"
        return 1
    fi
    
    echo "$version"
}

# Función para obtener versión desplegada desde ECR
get_deployed_version() {
    local service_name=$1
    local region=${2:-us-east-1}
    
    # Obtener el tag más reciente de ECR
    local latest_tag=$(aws ecr describe-images \
        --repository-name "$service_name" \
        --region "$region" \
        --query 'sort_by(imageDetails,&imagePushedAt)[-1].imageTags[0]' \
        --output text 2>/dev/null || echo "none")
    
    echo "$latest_tag"
}

# Función para comparar versiones
compare_versions() {
    local current_version=$1
    local deployed_version=$2
    
    if [ "$deployed_version" = "none" ] || [ "$deployed_version" = "None" ]; then
        echo "new"
        return
    fi
    
    if [ "$current_version" != "$deployed_version" ]; then
        echo "changed"
        return
    fi
    
    echo "unchanged"
}

# Función principal
detect_changes() {
    echo "🔍 Detectando servicios modificados..."
    echo "====================================="
    
    local services=("nit-validation-service" "user-service" "audit-service" "auth-service")
    local changed_services=()
    local region=${AWS_REGION:-us-east-1}
    
    for service in "${services[@]}"; do
        echo ""
        echo "📦 Analizando $service..."
        
        # Extraer versión actual
        local current_version=$(extract_version "$service")
        if [ $? -ne 0 ]; then
            echo "❌ Error extrayendo versión de $service"
            continue
        fi
        
        echo "   Versión actual: ${BLUE}$current_version${NC}"
        
        # Obtener versión desplegada
        local deployed_version=$(get_deployed_version "$service" "$region")
        echo "   Versión desplegada: ${BLUE}$deployed_version${NC}"
        
        # Comparar versiones
        local status=$(compare_versions "$current_version" "$deployed_version")
        
        case $status in
            "new")
                echo "   Estado: ${GREEN}NUEVO${NC} - Primera vez desplegando"
                changed_services+=("$service")
                ;;
            "changed")
                echo "   Estado: ${YELLOW}MODIFICADO${NC} - Versión actualizada"
                changed_services+=("$service")
                ;;
            "unchanged")
                echo "   Estado: ${BLUE}SIN CAMBIOS${NC} - No necesita despliegue"
                ;;
        esac
    done
    
    echo ""
    echo "📋 Resumen:"
    echo "==========="
    
    if [ ${#changed_services[@]} -eq 0 ]; then
        echo "✅ No hay servicios que necesiten despliegue"
        echo "CHANGED_SERVICES=[]" > .env.changes
    else
        echo "🚀 Servicios a desplegar:"
        for service in "${changed_services[@]}"; do
            echo "   - $service"
        done
        
        # Crear archivo con servicios modificados en formato JSON
        printf "CHANGED_SERVICES=[%s]\n" "$(printf '"%s",' "${changed_services[@]}" | sed 's/,$//')" > .env.changes
    fi
    
    echo ""
    echo "💾 Información guardada en .env.changes"
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  -h, --help     Mostrar esta ayuda"
    echo "  -r, --region   Especificar región AWS (default: us-east-1)"
    echo "  -v, --verbose  Mostrar información detallada"
    echo ""
    echo "Ejemplos:"
    echo "  $0                    # Detectar cambios con región por defecto"
    echo "  $0 -r us-west-2       # Detectar cambios en región us-west-2"
    echo "  $0 --verbose           # Mostrar información detallada"
}

# Parsear argumentos
VERBOSE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "❌ Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Ejecutar detección
detect_changes
