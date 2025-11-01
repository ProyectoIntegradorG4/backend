# Script para ejecutar pruebas del pedidos-service

param(
    [ValidateSet("all", "unit", "integration", "coverage")]
    [string]$TestType = "all",
    [switch]$Verbose,
    [switch]$ShowOutput
)

$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Pruebas - Pedidos Service" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "requirements.txt")) {
    Write-Host "Error: No se encontró requirements.txt" -ForegroundColor Red
    Write-Host "Ejecute este script desde el directorio pedidos-service" -ForegroundColor Yellow
    exit 1
}

# Crear entorno virtual si no existe
if (-not (Test-Path "venv")) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
}

# Activar entorno virtual
& ".\venv\Scripts\Activate.ps1"

# Instalar dependencias
Write-Host "Instalando dependencias..." -ForegroundColor Yellow
pip install -q -r requirements.txt

Write-Host ""
Write-Host "Ejecutando pruebas..." -ForegroundColor Green
Write-Host ""

$pytest_args = @("tests/", "-v", "--tb=short")

if ($Verbose) {
    $pytest_args += "-vv"
}

switch ($TestType) {
    "all" {
        Write-Host "Ejecutando todas las pruebas..." -ForegroundColor Cyan
        & pytest @pytest_args
    }
    "unit" {
        Write-Host "Ejecutando pruebas unitarias..." -ForegroundColor Cyan
        & pytest tests/test_pedidos.py -k "not integration" @pytest_args
    }
    "integration" {
        Write-Host "Ejecutando pruebas de integración..." -ForegroundColor Cyan
        & pytest tests/test_pedidos.py -k "integration" @pytest_args
    }
    "coverage" {
        Write-Host "Ejecutando pruebas con cobertura..." -ForegroundColor Cyan
        & pytest @pytest_args --cov=app --cov-report=html --cov-report=term
        Write-Host ""
        Write-Host "Reporte de cobertura generado en htmlcov/index.html" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Pruebas completadas" -ForegroundColor Green
