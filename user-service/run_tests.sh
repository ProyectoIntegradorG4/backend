#!/bin/bash
# Script para ejecutar tests unitarios del user-service

echo "=== TESTING USER SERVICE ==="
echo "1. Instalando dependencias de testing..."
pip install -r requirements-test.txt

echo "2. Ejecutando tests unitarios..."
pytest tests/ -v --tb=short

echo "3. Ejecutando tests con coverage..."
pytest tests/ --cov=app --cov-report=html --cov-report=term

echo "4. Tests completados. Ver coverage en htmlcov/index.html"