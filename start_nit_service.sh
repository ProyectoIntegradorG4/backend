#!/bin/bash

# Script de inicio rápido para NIT Validation Service
# Ejecutar desde el directorio backend/

echo "🚀 Iniciando NIT Validation Service en Docker"
echo "=============================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: No se encontró docker-compose.yml"
    echo "   Ejecutar desde el directorio backend/"
    exit 1
fi

# Construir e iniciar servicios
echo "📦 Construyendo servicios..."
docker-compose build nit-validation-service redis

echo "🔧 Iniciando dependencias (PostgreSQL y Redis)..."
docker-compose up -d postgres-db redis

echo "⏳ Esperando que las dependencias estén listas..."
sleep 10

echo "🚀 Iniciando NIT Validation Service..."
docker-compose up -d nit-validation-service

echo "⏳ Esperando que el servicio esté listo..."
sleep 5

# Verificar estado de los servicios
echo ""
echo "📊 Estado de los servicios:"
docker-compose ps postgres-db redis nit-validation-service

# Verificar health checks
echo ""
echo "🔍 Verificando health checks..."

# Health check PostgreSQL
if docker-compose exec postgres-db pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL: OK"
else
    echo "❌ PostgreSQL: No disponible"
fi

# Health check Redis
if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: OK"
else
    echo "❌ Redis: No disponible"
fi

# Health check NIT Service
if curl -f http://localhost:8002/health > /dev/null 2>&1; then
    echo "✅ NIT Validation Service: OK"
else
    echo "❌ NIT Validation Service: No disponible"
fi

echo ""
echo "🎉 ¡Servicios iniciados!"
echo ""
echo "📋 URLs disponibles:"
echo "   - NIT Validation Service: http://localhost:8002"
echo "   - Health Check: http://localhost:8002/health"
echo "   - API Docs: http://localhost:8002/docs"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "🧪 Para cargar datos de prueba:"
echo "   docker-compose exec nit-validation-service python load_sample_data.py"
echo ""
echo "🔧 Para ver logs:"
echo "   docker-compose logs -f nit-validation-service"
echo ""
echo "🛑 Para detener:"
echo "   docker-compose down"