#!/usr/bin/env python3
"""
Script de prueba para el servicio de autenticación
"""

import requests
import json
import sys

# Configuración
BASE_URL = "http://localhost:8004"
API_BASE = f"{BASE_URL}/api/v1"

def test_health():
    """Probar endpoint de salud"""
    print("🔍 Probando endpoint de salud...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("Servicio de autenticación está funcionando")
            print(f"   Respuesta: {response.json()}")
        else:
            print(f"Error en health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error conectando al servicio: {e}")
        return False
    return True

def test_login():
    """Probar endpoint de login"""
    print("\n🔍 Probando endpoint de login...")
    
    # Datos de prueba - Usuario admin
    login_data = {
        "email": "test1@google.com",
        "password": "Abc@1234"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Login exitoso!")
            print(f"   ID: {data.get('id')}")
            print(f"   Email: {data.get('email')}")
            print(f"   Full Name: {data.get('fullName')}")
            print(f"   Is Active: {data.get('isActive')}")
            print(f"   Roles: {data.get('roles')}")
            print(f"   Token: {data.get('token')[:50]}...")
            return data.get('token')
        else:
            print(f"Error en login: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error en login: {e}")
        return None

def test_verify_token(token):
    """Probar verificación de token"""
    if not token:
        print("\n⏭Saltando verificación de token (no hay token)")
        return
        
    print("\nProbando verificación de token...")
    
    try:
        response = requests.get(
            f"{API_BASE}/verify-token",
            params={"token": token}
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Token válido!")
            print(f"   User ID: {data.get('user_id')}")
            print(f"   Email: {data.get('email')}")
            print(f"   Roles: {data.get('roles')}")
        else:
            print(f"Error verificando token: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except Exception as e:
        print(f" Error verificando token: {e}")

def test_other_users():
    """Probar login con otros usuarios de prueba"""
    print("\n Probando login con otros usuarios...")
    
    test_users = [
        {
            "email": "maria@test.com",
            "password": "Test@1234",
            "name": "María García"
        },
        {
            "email": "pedro@test.com", 
            "password": "Password@1234",
            "name": "Pedro López"
        }
    ]
    
    for user in test_users:
        print(f"\n   Probando usuario: {user['name']} ({user['email']})")
        try:
            response = requests.post(
                f"{API_BASE}/login",
                json={"email": user["email"], "password": user["password"]},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Login exitoso para {user['name']}")
                print(f"   Rol: {data.get('roles', [])}")
            else:
                print(f"   Error en login: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                
        except Exception as e:
            print(f"   Error en login: {e}")

def test_invalid_login():
    """Probar login con credenciales inválidas"""
    print("\nProbando login con credenciales inválidas...")
    
    login_data = {
        "email": "invalid@test.com",
        "password": "wrongpassword"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("Correctamente rechazó credenciales inválidas")
        else:
            print(f"Debería haber devuelto 401, pero devolvió: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except Exception as e:
        print(f"Error en test de credenciales inválidas: {e}")

def main():
    """Función principal de pruebas"""
    print("Iniciando pruebas del servicio de autenticación")
    print("=" * 50)
    
    # Verificar que el servicio esté funcionando
    if not test_health():
        print("\nEl servicio no está funcionando. Asegúrate de que esté ejecutándose.")
        sys.exit(1)
    
    # Probar login
    token = test_login()
    
    # Probar verificación de token
    test_verify_token(token)
    
    # Probar otros usuarios
    test_other_users()
    
    # Probar login inválido
    test_invalid_login()
    
    print("\n" + "=" * 50)
    print("Pruebas completadas")

if __name__ == "__main__":
    main()
