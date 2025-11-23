"""
Script de prueba para verificar la generación de rutas
"""
import requests
import json

BASE_URL = "http://localhost:8007/api/v1/logistica"

# Headers de autenticación
HEADERS = {
    "Content-Type": "application/json",
    "usuario-id": "1",
    "rol-usuario": "admin",
    "nit-usuario": "111111111-1"
}

def test_health():
    """Verificar que el servicio está activo"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_generar_rutas():
    """Probar generación de rutas con datos de ejemplo"""
    
    # Datos de prueba: 2 vehículos, 5 pedidos
    request_data = {
        "objetivo": "min_distancia",
        "vehiculos": [
            {
                "id": "VEH-001",
                "capacidad_volumen": 50.0,
                "capacidad_peso": 1000.0,
                "cadena_frio": True,
                "depot": {
                    "lat": 4.6097,
                    "lon": -74.0817
                },
                "duracion_maxima_minutos": 480
            },
            {
                "id": "VEH-002",
                "capacidad_volumen": 30.0,
                "capacidad_peso": 600.0,
                "cadena_frio": False,
                "depot": {
                    "lat": 4.6097,
                    "lon": -74.0817
                },
                "duracion_maxima_minutos": 360
            }
        ],
        "pedidos": [
            {
                "id": "PED-001",
                "lat": 4.6351,
                "lon": -74.0703,
                "ventana_inicio": "08:00",
                "ventana_fin": "12:00",
                "tiempo_servicio_minutos": 15,
                "requiere_frio": True,
                "volumen": 5.0,
                "peso": 50.0
            },
            {
                "id": "PED-002",
                "lat": 4.6762,
                "lon": -74.0481,
                "ventana_inicio": "09:00",
                "ventana_fin": "13:00",
                "tiempo_servicio_minutos": 20,
                "requiere_frio": False,
                "volumen": 3.0,
                "peso": 30.0
            },
            {
                "id": "PED-003",
                "lat": 4.6420,
                "lon": -74.1100,
                "ventana_inicio": "10:00",
                "ventana_fin": "14:00",
                "tiempo_servicio_minutos": 10,
                "requiere_frio": True,
                "volumen": 7.0,
                "peso": 80.0
            },
            {
                "id": "PED-004",
                "lat": 4.5981,
                "lon": -74.0758,
                "ventana_inicio": "08:30",
                "ventana_fin": "11:30",
                "tiempo_servicio_minutos": 15,
                "requiere_frio": False,
                "volumen": 4.0,
                "peso": 40.0
            },
            {
                "id": "PED-005",
                "lat": 4.6530,
                "lon": -74.0920,
                "ventana_inicio": "11:00",
                "ventana_fin": "15:00",
                "tiempo_servicio_minutos": 25,
                "requiere_frio": True,
                "volumen": 6.0,
                "peso": 70.0
            }
        ],
        "limites": {
            "max_distancia_km": 100.0,
            "max_duracion_minutos": 480,
            "considerar_trafico": False
        }
    }
    
    print("\n=== GENERANDO RUTAS ===")
    print(f"Vehículos: {len(request_data['vehiculos'])}")
    print(f"Pedidos: {len(request_data['pedidos'])}")
    
    response = requests.post(
        f"{BASE_URL}/rutas/generar",
        headers=HEADERS,
        json=request_data
    )
    
    print(f"\nStatus code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nTiempo de cálculo: {result['tiempo_calculo_ms']}ms")
        print(f"Rutas generadas: {len(result['rutas'])}")
        
        for i, ruta in enumerate(result['rutas'], 1):
            print(f"\n--- Ruta {i} ---")
            print(f"Vehículo: {ruta['vehiculo_id']}")
            print(f"Paradas: {len(ruta['paradas'])}")
            print(f"Distancia: {ruta['distancia_km']} km")
            print(f"Duración: {ruta['duracion_minutos']} min")
            print(f"Uso capacidad: {ruta['uso_capacidad']['porcentaje']}%")
            print(f"Secuencia: {' -> '.join(ruta['orden'])}")
            
            if ruta.get('paradas'):
                print("\nParadas:")
                for parada in ruta['paradas']:
                    cumple = "✓" if parada['cumple_ventana'] else "✗"
                    print(f"  {parada['orden']}. {parada['pedido_id']} "
                          f"ETA: {parada['eta']} "
                          f"Ventana: {parada['ventana_inicio']}-{parada['ventana_fin']} {cumple}")
        
        if result.get('warnings'):
            print("\n⚠️  Advertencias:")
            for warning in result['warnings']:
                print(f"  - {warning}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

def test_crear_vehiculo():
    """Probar creación de vehículo"""
    
    vehiculo_data = {
        "vehiculo_id": "VEH-TEST-001",
        "nombre": "Camión Refrigerado Grande",
        "capacidad_volumen": 60.0,
        "capacidad_peso": 1500.0,
        "cadena_frio": True,
        "depot_latitud": 4.6097,
        "depot_longitud": -74.0817,
        "depot_direccion": "Calle 26 #68-90, Bogotá",
        "duracion_maxima_minutos": 540
    }
    
    print("\n=== CREANDO VEHÍCULO ===")
    print(f"ID: {vehiculo_data['vehiculo_id']}")
    print(f"Nombre: {vehiculo_data['nombre']}")
    
    response = requests.post(
        f"{BASE_URL}/vehiculos",
        headers=HEADERS,
        json=vehiculo_data
    )
    
    print(f"\nStatus code: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"Vehículo creado exitosamente:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 201

def test_listar_vehiculos():
    """Probar listado de vehículos"""
    
    print("\n=== LISTANDO VEHÍCULOS ===")
    
    response = requests.get(
        f"{BASE_URL}/vehiculos",
        headers=HEADERS,
        params={"solo_activos": True}
    )
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nTotal de vehículos: {result['total']}")
        
        for vehiculo in result['vehiculos']:
            print(f"\n- {vehiculo['vehiculo_id']}: {vehiculo['nombre']}")
            print(f"  Capacidad: {vehiculo['capacidad_volumen']}m³ / {vehiculo['capacidad_peso']}kg")
            print(f"  Cadena frío: {'Sí' if vehiculo['cadena_frio'] else 'No'}")
            print(f"  Depot: ({vehiculo['depot_latitud']}, {vehiculo['depot_longitud']})")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBAS DE GENERACIÓN DE RUTAS - HU-WEB-012")
    print("=" * 60)
    
    try:
        # 1. Verificar que el servicio está activo
        if not test_health():
            print("\n❌ El servicio no está disponible")
            exit(1)
        
        # 2. Probar generación de rutas
        print("\n" + "=" * 60)
        test_generar_rutas()
        
        print("\n" + "=" * 60)
        print("\n✅ Pruebas completadas")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se pudo conectar al servicio en http://localhost:8007")
        print("Asegúrate de que el servicio esté corriendo con: python main.py")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
