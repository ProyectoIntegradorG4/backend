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
    print("🔧 Configurando datos de prueba...")
    
    try:
        # Conectar a la base de datos
        conn = psycopg.connect(DATABASE_URL)
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
            print("❌ La tabla 'usuarios' no existe. Asegúrate de que el user-service esté configurado.")
            return False
        
        # Crear datos de prueba
        test_users = [
            {
                "nombre": "Juan Carlos",
                "correo_electronico": "test1@google.com",
                "password": "Abc123",
                "nit": "123456789",
                "rol": "admin"
            },
            {
                "nombre": "María García",
                "correo_electronico": "maria@test.com",
                "password": "Test123",
                "nit": "987654321",
                "rol": "usuario_institucional"
            },
            {
                "nombre": "Pedro López",
                "correo_electronico": "pedro@test.com",
                "password": "Password123",
                "nit": "456789123",
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
                print(f"   ⏭️  Usuario {user['correo_electronico']} ya existe, actualizando...")
                # Actualizar contraseña
                hashed_password = hash_password(user["password"])
                cur.execute("""
                    UPDATE usuarios 
                    SET password_hash = %s, rol = %s, activo = true
                    WHERE correo_electronico = %s
                """, (hashed_password, user["rol"], user["correo_electronico"]))
            else:
                print(f"   ➕ Creando usuario {user['correo_electronico']}...")
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
        
        print("✅ Datos de prueba configurados correctamente")
        
        # Mostrar usuarios creados
        cur.execute("""
            SELECT id, nombre, correo_electronico, rol, activo 
            FROM usuarios 
            WHERE correo_electronico IN %s
            ORDER BY id
        """, (tuple([user["correo_electronico"] for user in test_users]),))
        
        users = cur.fetchall()
        print("\n📋 Usuarios disponibles para pruebas:")
        for user in users:
            print(f"   ID: {user[0]}, Email: {user[2]}, Rol: {user[3]}, Activo: {user[4]}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error configurando datos de prueba: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Configuración de datos de prueba para Auth Service")
    print("=" * 60)
    
    if setup_test_data():
        print("\n🎉 Configuración completada exitosamente!")
        print("\nPuedes probar el servicio con:")
        print("   python test_auth.py")
    else:
        print("\n❌ Error en la configuración")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
