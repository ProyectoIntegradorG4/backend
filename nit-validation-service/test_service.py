"""
Script de prueba para el NIT Validation Service
"""
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8002/api/v1"

def test_health_check():
    """Probar el endpoint de health check"""
    print("🔍 Probando health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_nit_validation_post(nit: str, pais: str = None):
    """Probar validación de NIT usando POST"""
    print(f"\n🔍 Probando validación POST para NIT: {nit}")
    
    payload = {"nit": nit}
    if pais:
        payload["pais"] = pais
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/validate", json=payload)
        end_time = time.time()
        
        print(f"Status: {response.status_code}")
        print(f"Tiempo de respuesta: {(end_time - start_time) * 1000:.2f}ms")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code in [200, 404, 400]
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_nit_validation_get(nit: str, pais: str = None):
    """Probar validación de NIT usando GET"""
    print(f"\n🔍 Probando validación GET para NIT: {nit}")
    
    url = f"{BASE_URL}/validate/{nit}"
    params = {}
    if pais:
        params["pais"] = pais
    
    try:
        start_time = time.time()
        response = requests.get(url, params=params)
        end_time = time.time()
        
        print(f"Status: {response.status_code}")
        print(f"Tiempo de respuesta: {(end_time - start_time) * 1000:.2f}ms")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code in [200, 404, 400]
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_institution_details(nit: str):
    """Probar obtención de detalles de institución"""
    print(f"\n🔍 Probando detalles de institución para NIT: {nit}")
    
    try:
        response = requests.get(f"{BASE_URL}/institution/{nit}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code in [200, 404]
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cache_operations(nit: str):
    """Probar operaciones de caché"""
    print(f"\n🔍 Probando operaciones de caché...")
    
    try:
        # Obtener estadísticas del caché
        print("📊 Estadísticas del caché:")
        response = requests.get(f"{BASE_URL}/cache/stats")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Limpiar caché para un NIT
        print(f"\n🧹 Limpiando caché para NIT: {nit}")
        response = requests.delete(f"{BASE_URL}/cache/{nit}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_performance(nit: str, iterations: int = 5):
    """Probar rendimiento con múltiples llamadas"""
    print(f"\n⚡ Probando rendimiento con {iterations} iteraciones para NIT: {nit}")
    
    times = []
    
    for i in range(iterations):
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/validate/{nit}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            times.append(response_time)
            
            cache_status = "HIT" if response_time < 50 else "MISS"
            print(f"Iteración {i+1}: {response_time:.2f}ms ({cache_status})")
            
        except Exception as e:
            print(f"❌ Error en iteración {i+1}: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📈 Estadísticas de rendimiento:")
        print(f"   - Tiempo promedio: {avg_time:.2f}ms")
        print(f"   - Tiempo mínimo: {min_time:.2f}ms")
        print(f"   - Tiempo máximo: {max_time:.2f}ms")

def run_test_suite():
    """Ejecutar suite completa de pruebas"""
    print("🚀 Iniciando suite de pruebas para NIT Validation Service")
    print("=" * 60)
    
    # NITs de prueba del archivo JSON
    test_nits = [
        {"nit": "4347402554", "pais": "Colombia", "expected": "valid"},  # Activo
        {"nit": "1927250080", "pais": "Colombia", "expected": "inactive"},  # Inactivo
        {"nit": "7572516483", "pais": "Peru", "expected": "valid"},  # Activo
        {"nit": "9999999999", "pais": "Colombia", "expected": "not_found"},  # No existe
        {"nit": "invalid", "pais": None, "expected": "invalid_format"},  # Formato inválido
    ]
    
    results = {}
    
    # 1. Health check
    results["health"] = test_health_check()
    
    # 2. Probar validaciones
    for test_case in test_nits:
        nit = test_case["nit"]
        pais = test_case["pais"]
        
        # POST
        results[f"post_{nit}"] = test_nit_validation_post(nit, pais)
        
        # GET
        results[f"get_{nit}"] = test_nit_validation_get(nit, pais)
        
        # Detalles de institución (solo para NITs válidos)
        if test_case["expected"] in ["valid", "inactive"]:
            results[f"details_{nit}"] = test_institution_details(nit)
    
    # 3. Operaciones de caché
    results["cache"] = test_cache_operations("4347402554")
    
    # 4. Prueba de rendimiento
    test_performance("4347402554")
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 Resultado final: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
    else:
        print(f"⚠️  {total - passed} pruebas fallaron")

if __name__ == "__main__":
    print("Asegúrate de que el servicio esté ejecutándose en http://localhost:8002")
    input("Presiona Enter para continuar...")
    
    run_test_suite()