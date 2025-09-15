# Script de inicio rápido para NIT Validation Service (PowerShell)
# Ejecutar desde el directorio backend/

Write-Host "🚀 Iniciando NIT Validation Service en Docker" -ForegroundColor Green
Write-Host "=============================================="

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ Error: No se encontró docker-compose.yml" -ForegroundColor Red
    Write-Host "   Ejecutar desde el directorio backend/" -ForegroundColor Yellow
    exit 1
}

# Construir e iniciar servicios
Write-Host "📦 Construyendo servicios..." -ForegroundColor Blue
docker-compose build nit-validation-service redis

Write-Host "🔧 Iniciando dependencias (PostgreSQL y Redis)..." -ForegroundColor Blue
docker-compose up -d postgres-db redis

Write-Host "⏳ Esperando que las dependencias estén listas..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "🚀 Iniciando NIT Validation Service..." -ForegroundColor Blue
docker-compose up -d nit-validation-service

Write-Host "⏳ Esperando que el servicio esté listo..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verificar estado de los servicios
Write-Host ""
Write-Host "📊 Estado de los servicios:" -ForegroundColor Cyan
docker-compose ps postgres-db redis nit-validation-service

# Verificar health checks
Write-Host ""
Write-Host "🔍 Verificando health checks..." -ForegroundColor Cyan

# Health check PostgreSQL
try {
    $pgResult = docker-compose exec postgres-db pg_isready -U postgres 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL: OK" -ForegroundColor Green
    }
    else {
        Write-Host "❌ PostgreSQL: No disponible" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ PostgreSQL: No disponible" -ForegroundColor Red
}

# Health check Redis
try {
    $redisResult = docker-compose exec redis redis-cli ping 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Redis: OK" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Redis: No disponible" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ Redis: No disponible" -ForegroundColor Red
}

# Health check NIT Service
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8002/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ NIT Validation Service: OK" -ForegroundColor Green
    }
    else {
        Write-Host "❌ NIT Validation Service: No disponible" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ NIT Validation Service: No disponible" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 ¡Servicios iniciados!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 URLs disponibles:" -ForegroundColor Cyan
Write-Host "   - NIT Validation Service: http://localhost:8002" -ForegroundColor White
Write-Host "   - Health Check: http://localhost:8002/health" -ForegroundColor White
Write-Host "   - API Docs: http://localhost:8002/docs" -ForegroundColor White
Write-Host "   - PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "   - Redis: localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Para cargar datos de prueba:" -ForegroundColor Cyan
Write-Host "   docker-compose exec nit-validation-service python load_sample_data.py" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Para ver logs:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f nit-validation-service" -ForegroundColor White
Write-Host ""
Write-Host "🛑 Para detener:" -ForegroundColor Cyan
Write-Host "   docker-compose down" -ForegroundColor White