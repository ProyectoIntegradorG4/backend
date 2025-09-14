"""
Script para cargar datos de prueba en la tabla InstitucionesAsociadas
"""
import json
import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session

# Agregar el directorio raíz al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal, engine
from app.models.institucion import InstitucionAsociada, Base

def load_sample_data():
    """Cargar datos de muestra desde NITValidationData.json"""
    
    # Crear las tablas si no existen
    Base.metadata.create_all(bind=engine)
    
    # Leer datos del archivo JSON
    json_file_path = os.path.join(os.path.dirname(__file__), "NITValidationData.json")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {json_file_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error al leer el archivo JSON: {e}")
        return False
    
    # Crear sesión de base de datos
    db = SessionLocal()
    
    try:
        # Limpiar datos existentes (opcional)
        print("Limpiando datos existentes...")
        db.query(InstitucionAsociada).delete()
        
        # Cargar nuevos datos
        print(f"Cargando {len(data)} instituciones...")
        instituciones_cargadas = 0
        
        for item in data:
            try:
                # Parsear fecha_registro
                fecha_registro = datetime.strptime(item["fecha_registro"], "%m/%d/%Y")
                
                # Crear nueva institución
                institucion = InstitucionAsociada(
                    nit=item["nit"],
                    nombre_institucion=item["nombre_institucion"],
                    pais=item["pais"],
                    fecha_registro=fecha_registro,
                    activo=item["activo"]
                )
                
                db.add(institucion)
                instituciones_cargadas += 1
                
            except Exception as e:
                print(f"Error procesando institución {item.get('nit', 'unknown')}: {e}")
                continue
        
        # Confirmar cambios
        db.commit()
        print(f"✅ Datos cargados exitosamente: {instituciones_cargadas} instituciones")
        
        # Mostrar estadísticas
        total_activas = db.query(InstitucionAsociada).filter(InstitucionAsociada.activo == True).count()
        total_inactivas = db.query(InstitucionAsociada).filter(InstitucionAsociada.activo == False).count()
        
        print(f"📊 Estadísticas:")
        print(f"   - Total instituciones: {instituciones_cargadas}")
        print(f"   - Instituciones activas: {total_activas}")
        print(f"   - Instituciones inactivas: {total_inactivas}")
        
        # Mostrar distribución por país
        paises = db.query(InstitucionAsociada.pais, db.func.count(InstitucionAsociada.nit)).group_by(InstitucionAsociada.pais).all()
        print(f"   - Distribución por país:")
        for pais, count in paises:
            print(f"     * {pais}: {count}")
        
        return True
        
    except Exception as e:
        print(f"Error cargando datos: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

def verify_data():
    """Verificar que los datos se cargaron correctamente"""
    db = SessionLocal()
    
    try:
        # Contar registros
        total_count = db.query(InstitucionAsociada).count()
        print(f"Total de registros en la base de datos: {total_count}")
        
        # Mostrar algunos ejemplos
        ejemplos = db.query(InstitucionAsociada).limit(5).all()
        print("\n📋 Ejemplos de registros:")
        for inst in ejemplos:
            print(f"   NIT: {inst.nit} | {inst.nombre_institucion} | {inst.pais} | Activo: {inst.activo}")
        
        return total_count > 0
        
    except Exception as e:
        print(f"Error verificando datos: {e}")
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Iniciando carga de datos de prueba para NIT Validation Service")
    print("=" * 60)
    
    # Cargar datos
    if load_sample_data():
        print("\n✅ Carga de datos completada exitosamente")
        
        # Verificar datos
        print("\n🔍 Verificando datos cargados...")
        if verify_data():
            print("✅ Verificación exitosa")
        else:
            print("❌ Error en la verificación")
    else:
        print("❌ Error en la carga de datos")
        sys.exit(1)
    
    print("\n🎉 Proceso completado!")