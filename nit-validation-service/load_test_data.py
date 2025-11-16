#!/usr/bin/env python3
"""
Script para cargar datos de prueba de instituciones asociadas
desde NITValidationData.json a la base de datos PostgreSQL
"""
import json
import sys
import os
from datetime import datetime
import psycopg

def parse_date(date_string):
    """Convierte fecha de formato M/D/YYYY a YYYY-MM-DD"""
    try:
        # Parsear formato M/D/YYYY o MM/DD/YYYY
        return datetime.strptime(date_string, "%m/%d/%Y").date()
    except ValueError:
        try:
            # Formato alternativo D/M/YYYY
            return datetime.strptime(date_string, "%d/%m/%Y").date()
        except ValueError:
            print(f"Error parsing date: {date_string}")
            return None

def load_test_data():
    """Carga datos de prueba desde NITValidationData.json"""
    
    # Configuración de base de datos
    DB_CONFIG = "postgresql://nit_service:nit_password@postgres-db:5432/nit_db"
    
    try:
        # Leer datos JSON
        json_file = 'NITValidationData.json'
        if not os.path.exists(json_file):
            print(f"Error: No se encontró el archivo {json_file}")
            return False
            
        with open(json_file, 'r', encoding='utf-8') as f:
            institutions = json.load(f)
        
        print(f"Cargando {len(institutions)} instituciones...")
        
        # Conectar a la base de datos
        conn = psycopg.connect(DB_CONFIG)
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instituciones_asociadas (
                nit VARCHAR(20) PRIMARY KEY,
                nombre_institucion VARCHAR(200) NOT NULL,
                pais VARCHAR(50) NOT NULL,
                fecha_registro DATE NOT NULL,
                activo BOOLEAN NOT NULL DEFAULT true
            )
        """)
        
        # Insertar datos
        success_count = 0
        error_count = 0
        
        for inst in institutions:
            try:
                fecha_registro = parse_date(inst['fecha_registro'])
                if fecha_registro is None:
                    error_count += 1
                    continue
                
                cursor.execute("""
                    INSERT INTO instituciones_asociadas 
                    (nit, nombre_institucion, pais, fecha_registro, activo)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (nit) DO UPDATE SET
                        nombre_institucion = EXCLUDED.nombre_institucion,
                        pais = EXCLUDED.pais,
                        fecha_registro = EXCLUDED.fecha_registro,
                        activo = EXCLUDED.activo
                """, (
                    inst['nit'],
                    inst['nombre_institucion'],
                    inst['pais'],
                    fecha_registro,
                    inst['activo']
                ))
                success_count += 1
                
            except Exception as e:
                print(f"Error insertando {inst['nit']}: {str(e)}")
                error_count += 1
        
        conn.commit()
        
        # Verificar carga
        cursor.execute("SELECT COUNT(*) as total FROM instituciones_asociadas")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as activos FROM instituciones_asociadas WHERE activo = true")
        active_records = cursor.fetchone()[0]
        
        print(f"\n✅ Carga completada:")
        print(f"   - Registros insertados: {success_count}")
        print(f"   - Errores: {error_count}")
        print(f"   - Total en BD: {total_records}")
        print(f"   - NITs activos: {active_records}")
        
        # Mostrar algunos ejemplos
        cursor.execute("""
            SELECT nit, nombre_institucion, pais, activo 
            FROM instituciones_asociadas 
            LIMIT 5
        """)
        examples = cursor.fetchall()
        
        print(f"\n📋 Ejemplos de datos cargados:")
        for row in examples:
            status = "✅" if row[3] else "❌"
            print(f"   {status} {row[0]} - {row[1]} ({row[2]})")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg.Error as e:
        print(f"Error de base de datos: {str(e)}")
        return False
    except Exception as e:
        print(f"Error general: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando carga de datos de prueba...")
    success = load_test_data()
    if success:
        print("\n🎉 ¡Datos cargados exitosamente!")
        sys.exit(0)
    else:
        print("\n❌ Error en la carga de datos")
        sys.exit(1)