# Script de PowerShell para iniciar el servicio de autenticación
# Uso: .\start_auth_service.ps1

Write-Host "🚀 Iniciando Auth Service - MediSupply" -ForegroundColor Green
Write-Host "=" * 50

# Verificar si Docker está ejecutándose
Write-Host "🔍 Verificando Docker..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker está ejecutándose" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker no está ejecutándose. Por favor, inicia Docker Desktop." -ForegroundColor Red
    exit 1
}

# Verificar si el archivo .env existe
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Archivo .env no encontrado. Copiando desde example.env..." -ForegroundColor Yellow
    Copy-Item "example.env" ".env"
    Write-Host "✅ Archivo .env creado" -ForegroundColor Green
}

# Construir y ejecutar el servicio de autenticación
Write-Host "🔨 Construyendo Auth Service..." -ForegroundColor Yellow
docker-compose build auth-service

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error construyendo el servicio" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Servicio construido correctamente" -ForegroundColor Green

# Ejecutar el servicio
Write-Host "🚀 Iniciando Auth Service..." -ForegroundColor Yellow
docker-compose up auth-service

Write-Host "🏁 Auth Service detenido" -ForegroundColor Green
