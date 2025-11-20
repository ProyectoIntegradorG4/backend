# Script para ejecutar tests de visita-service
# Ejecutar desde: backend/visita-service/

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Visita Service - Test Suite" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "main.py")) {
    Write-Host "❌ Error: Debes ejecutar este script desde backend/visita-service/" -ForegroundColor Red
    exit 1
}

# Verificar que pytest está instalado
Write-Host "🔍 Verificando dependencias..." -ForegroundColor Yellow
$pytestInstalled = pip list | Select-String "pytest"

if (-not $pytestInstalled) {
    Write-Host "⚠️  pytest no está instalado. Instalando dependencias..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host "✅ Dependencias verificadas" -ForegroundColor Green
Write-Host ""

# Ejecutar tests
Write-Host "🧪 Ejecutando tests..." -ForegroundColor Yellow
Write-Host ""

# Ejecutar suite completo con alta cobertura
pytest tests/test_ruta_optimizer.py tests/test_visita_service_unit.py tests/test_visitas_routes_simple.py tests/test_error_handling.py -v --tb=short --cov=app --cov-report=term-missing --cov-report=html

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "  ✅ Todos los tests pasaron" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Reporte de cobertura guardado en:" -ForegroundColor Yellow
    Write-Host "   htmlcov/index.html" -ForegroundColor Cyan
} else {
    Write-Host "  ❌ Algunos tests fallaron" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
}

Write-Host ""

exit $exitCode

