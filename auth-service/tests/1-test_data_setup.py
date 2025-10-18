#!/usr/bin/env python3
"""
Script para configurar datos de prueba en la base de datos
"""

import psycopg
import os
import bcrypt
from datetime import datetime, timezone

# Configuración de la base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user_service:user_password@localhost:5432/user_db"
)

def hash_password(password: str) -> str:
    """Hash de contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def setup_test_data():
    """Configurar datos de prueba en la base de datos"""
    print("Configurando datos de prueba...")
    
    try:
        # Ajustar cadena para psycopg si es necesario
        db_url = DATABASE_URL.replace('postgresql+psycopg://', 'postgresql://')
        conn = psycopg.connect(db_url)
        cur = conn.cursor()
        
        # Verificar si la tabla existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'usuarios'
            );
        """)
        
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("La tabla 'usuarios' no existe. Asegúrate de que el user-service esté configurado.")
            return False
        
        # Crear datos de prueba
        test_users = [
            {
                "nombre": "Juan Carlos",
                "correo_electronico": "test1@google.com",
                "password": "Abc@1234",
                "nit": "83-102-2959",
                "rol": "admin"
            },
            {
                "nombre": "María García",
                "correo_electronico": "maria@test.com",
                "password": "Test@1234",
                "nit": "89-078-5710",
                "rol": "usuario_institucional"
            },
            {
                "nombre": "Pedro López",
                "correo_electronico": "pedro@test.com",
                "password": "Password@1234",
                "nit": "94-974-6914",
                "rol": "usuario_institucional"
            }
        ]
        
        for user in test_users:
            # Verificar si el usuario ya existe
            cur.execute("""
                SELECT id FROM usuarios WHERE correo_electronico = %s
            """, (user["correo_electronico"],))
            
            existing_user = cur.fetchone()
            
            if existing_user:
                print(f"Usuario {user['correo_electronico']} ya existe, actualizando...")
                # Actualizar contraseña
                hashed_password = hash_password(user["password"])
                cur.execute("""
                    UPDATE usuarios 
                    SET password_hash = %s, rol = %s, activo = true
                    WHERE correo_electronico = %s
                """, (hashed_password, user["rol"], user["correo_electronico"]))
            else:
                print(f"Creando usuario {user['correo_electronico']}...")
                # Crear nuevo usuario
                hashed_password = hash_password(user["password"])
                cur.execute("""
                    INSERT INTO usuarios (nombre, correo_electronico, password_hash, nit, rol, activo, fecha_registro)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    user["nombre"],
                    user["correo_electronico"],
                    hashed_password,
                    user["nit"],
                    user["rol"],
                    True,
                    datetime.now(timezone.utc)
                ))
        
        # Confirmar cambios
        conn.commit()
        
        print("Datos de prueba configurados correctamente")
        
        # Mostrar usuarios creados
        emails = [user["correo_electronico"] for user in test_users]
        placeholders = ','.join(['%s'] * len(emails))
        cur.execute(f"""
            SELECT id, nombre, correo_electronico, rol, activo 
            FROM usuarios 
            WHERE correo_electronico IN ({placeholders})
            ORDER BY id
        """, emails)
        
        users = cur.fetchall()
        print("\nUsuarios disponibles para pruebas:")
        for user in users:
            print(f"   ID: {user[0]}, Email: {user[2]}, Rol: {user[3]}, Activo: {user[4]}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error configurando datos de prueba: {e}")
        return False

def main():
    """Función principal"""
    print("Configuración de datos de prueba para Auth Service")
    print("=" * 60)
    
    if setup_test_data():
        print("\nConfiguración completada exitosamente!")
        print("\nPuedes probar el servicio con:")
        print("   python test_auth.py")
    else:
        print("\nError en la configuración")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
