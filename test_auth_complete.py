#!/usr/bin/env python3
"""
Script completo de prueba para el servicio de autenticación
Incluye configuración de datos de prueba y pruebas de funcionalidad
"""

import requests
import json
import sys
import time
import subprocess
import os
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:8004"
API_BASE = f"{BASE_URL}/api/v1"
MAX_RETRIES = 30
RETRY_DELAY = 2

def wait_for_service():
    """Esperar a que el servicio esté disponible"""
    print("⏳ Esperando a que el servicio esté disponible...")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Servicio disponible")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < MAX_RETRIES - 1:
            print(f"   Intento {attempt + 1}/{MAX_RETRIES} - Esperando {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
    
    print("❌ Servicio no disponible después de todos los intentos")
    return False

def setup_test_data():
    """Configurar datos de prueba"""
    print("🔧 Configurando datos de prueba...")
    
    try:
        # Ejecutar script de configuración de datos
        result = subprocess.run([
            sys.executable, 
            "auth-service/test_data_setup.py"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Datos de prueba configurados")
            return True
        else:
            print(f"❌ Error configurando datos: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error ejecutando configuración: {e}")
        return False

def test_health():
    """Probar endpoint de salud"""
    print("\n🔍 Probando endpoint de salud...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Servicio de autenticación está funcionando")
            print(f"   Respuesta: {response.json()}")
            return True
        else:
            print(f"❌ Error en health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servicio: {e}")
        return False

def test_login_success():
    """Probar login exitoso"""
    print("\n🔍 Probando login exitoso...")
    
    test_cases = [
        {
            "email": "test1@google.com",
            "password": "Abc123",
            "expected_role": "admin"
        },
        {
            "email": "maria@test.com", 
            "password": "Test123",
            "expected_role": "usuario_institucional"
        }
    ]
    
    tokens = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"   Caso {i}: {case['email']}")
        
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                json={"email": case["email"], "password": case["password"]},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Login exitoso!")
                print(f"      ID: {data.get('id')}")
                print(f"      Email: {data.get('email')}")
                print(f"      Full Name: {data.get('fullName')}")
                print(f"      Is Active: {data.get('isActive')}")
                print(f"      Roles: {data.get('roles')}")
                
                # Verificar rol esperado
                if case["expected_role"] in data.get('roles', []):
                    print(f"      ✅ Rol correcto: {case['expected_role']}")
                else:
                    print(f"      ⚠️  Rol inesperado. Esperado: {case['expected_role']}, Obtenido: {data.get('roles')}")
                
                tokens.append(data.get('token'))
            else:
                print(f"   ❌ Error en login: {response.status_code}")
                print(f"      Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error en login: {e}")
            return False
    
    return tokens

def test_login_failure():
    """Probar login con credenciales inválidas"""
    print("\n🔍 Probando login con credenciales inválidas...")
    
    test_cases = [
        {
            "email": "nonexistent@test.com",
            "password": "wrongpassword",
            "description": "Usuario inexistente"
        },
        {
            "email": "test1@google.com",
            "password": "wrongpassword",
            "description": "Contraseña incorrecta"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"   Caso {i}: {case['description']}")
        
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                json={"email": case["email"], "password": case["password"]},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 401:
                print(f"   ✅ Correctamente rechazó credenciales inválidas")
            else:
                print(f"   ❌ Debería haber devuelto 401, pero devolvió: {response.status_code}")
                print(f"      Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error en test de credenciales inválidas: {e}")
            return False
    
    return True

def test_token_verification(tokens):
    """Probar verificación de tokens"""
    if not tokens:
        print("\n⏭️  Saltando verificación de token (no hay tokens)")
        return True
        
    print("\n🔍 Probando verificación de tokens...")
    
    for i, token in enumerate(tokens, 1):
        print(f"   Token {i}: {token[:20]}...")
        
        try:
            response = requests.get(
                f"{API_BASE}/auth/verify-token",
                params={"token": token}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Token válido!")
                print(f"      User ID: {data.get('user_id')}")
                print(f"      Email: {data.get('email')}")
                print(f"      Roles: {data.get('roles')}")
            else:
                print(f"   ❌ Error verificando token: {response.status_code}")
                print(f"      Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error verificando token: {e}")
            return False
    
    return True

def test_invalid_token():
    """Probar verificación de token inválido"""
    print("\n🔍 Probando verificación de token inválido...")
    
    invalid_tokens = [
        "invalid.token.here",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
        ""
    ]
    
    for i, token in enumerate(invalid_tokens, 1):
        print(f"   Token inválido {i}: {token[:20] if token else 'vacío'}...")
        
        try:
            response = requests.get(
                f"{API_BASE}/auth/verify-token",
                params={"token": token}
            )
            
            if response.status_code == 401:
                print(f"   ✅ Correctamente rechazó token inválido")
            else:
                print(f"   ❌ Debería haber devuelto 401, pero devolvió: {response.status_code}")
                print(f"      Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error verificando token inválido: {e}")
            return False
    
    return True

def main():
    """Función principal de pruebas"""
    print("🚀 Pruebas completas del servicio de autenticación")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not Path("auth-service").exists():
        print("❌ No se encontró el directorio auth-service. Ejecuta desde el directorio backend.")
        return 1
    
    # Configurar datos de prueba
    if not setup_test_data():
        print("❌ Error configurando datos de prueba")
        return 1
    
    # Esperar a que el servicio esté disponible
    if not wait_for_service():
        print("❌ El servicio no está disponible")
        return 1
    
    # Ejecutar pruebas
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Health check
    if test_health():
        tests_passed += 1
    
    # Test 2: Login exitoso
    tokens = test_login_success()
    if tokens:
        tests_passed += 1
    
    # Test 3: Login fallido
    if test_login_failure():
        tests_passed += 1
    
    # Test 4: Verificación de tokens
    if test_token_verification(tokens):
        tests_passed += 1
    
    # Test 5: Token inválido
    if test_invalid_token():
        tests_passed += 1
    
    # Resumen
    print("\n" + "=" * 60)
    print(f"📊 Resumen de pruebas: {tests_passed}/{total_tests} pasaron")
    
    if tests_passed == total_tests:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        return 0
    else:
        print("❌ Algunas pruebas fallaron")
        return 1

if __name__ == "__main__":
    exit(main())
