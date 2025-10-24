"""
Script simple para probar el servicio de proveedores
Ejecutar después de que el contenedor esté corriendo
"""
import httpx
import json
import time

BASE_URL = "http://localhost:8005/api/v1/proveedores"

def print_response(response, title=""):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, default=str))
    except:
        print(response.text)
    print(f"{'='*60}\n")

def test_service():
    """Ejecutar pruebas básicas del servicio"""
    
    print("🚀 Iniciando pruebas del servicio de proveedores...")
    
    # Esperar a que el servicio esté listo
    max_retries = 10
    for i in range(max_retries):
        try:
            response = httpx.get(f"{BASE_URL.replace('/api/v1/proveedores', '')}/health", timeout=2)
            if response.status_code == 200:
                print("✓ Servicio disponible")
                break
        except:
            if i < max_retries - 1:
                print(f"Esperando servicio... ({i+1}/{max_retries})")
                time.sleep(2)
    
    # 1. Listar proveedores iniciales
    print("\n1️⃣  Listando proveedores iniciales...")
    response = httpx.get(BASE_URL)
    print_response(response, "GET /proveedores")
    
    # 2. Crear un nuevo proveedor
    print("2️⃣  Creando un nuevo proveedor...")
    nuevo_proveedor = {
        "razon_social": "Proveedor de Prueba",
        "nit": "123456789-1",
        "tipo_proveedor": "laboratorio",
        "email": "prueba@proveedor.com",
        "telefono": "+57-1-1234567",
        "direccion": "Calle Principal 123",
        "ciudad": "Bogotá",
        "pais": "colombia",
        "certificaciones": ["ISO 9001:2015"],
        "estado": "activo",
        "calificacion": 4.0,
        "tiempo_entrega_promedio": 5
    }
    response = httpx.post(BASE_URL, json=nuevo_proveedor)
    print_response(response, "POST /proveedores")
    
    if response.status_code == 201:
        proveedor_creado = response.json()
        proveedor_id = proveedor_creado["proveedor_id"]
        
        # 3. Obtener el proveedor creado
        print("3️⃣  Obteniendo el proveedor creado...")
        response = httpx.get(f"{BASE_URL}/{proveedor_id}")
        print_response(response, f"GET /proveedores/{proveedor_id}")
        
        # 4. Actualizar el proveedor
        print("4️⃣  Actualizando el proveedor...")
        actualizacion = {
            "calificacion": 4.5,
            "tiempo_entrega_promedio": 3
        }
        response = httpx.put(f"{BASE_URL}/{proveedor_id}", json=actualizacion)
        print_response(response, f"PUT /proveedores/{proveedor_id}")
        
        # 5. Buscar proveedores
        print("5️⃣  Buscando proveedores por tipo...")
        response = httpx.get(f"{BASE_URL}/search/?tipo_proveedor=laboratorio")
        print_response(response, "GET /proveedores/search/?tipo_proveedor=laboratorio")
        
        # 6. Listar nuevamente
        print("6️⃣  Listando proveedores nuevamente...")
        response = httpx.get(BASE_URL)
        print_response(response, "GET /proveedores")
        
        # 7. Eliminar el proveedor
        print("7️⃣  Eliminando el proveedor...")
        response = httpx.delete(f"{BASE_URL}/{proveedor_id}")
        print_response(response, f"DELETE /proveedores/{proveedor_id}")
        
        # 8. Verificar que fue eliminado
        print("8️⃣  Verificando que el proveedor fue eliminado...")
        response = httpx.get(f"{BASE_URL}/{proveedor_id}")
        print_response(response, f"GET /proveedores/{proveedor_id} (debe retornar 404)")
    
    print("\n✅ Pruebas completadas\n")

if __name__ == "__main__":
    try:
        test_service()
    except Exception as e:
        print(f"❌ Error durante las pruebas: {str(e)}")
