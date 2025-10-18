#!/usr/bin/env python3
"""
Script para limpiar datos de prueba de la base de datos
"""

import psycopg
import os
import sys

# Configuración de la base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user_service:user_password@localhost:5432/user_db"
)

def clean_test_data():
    """Limpiar datos de prueba de la base de datos"""
    print("Limpiando datos de prueba...")
    
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
            print("La tabla 'usuarios' no existe.")
            return False
        
        # Lista de emails de usuarios de prueba
        test_emails = [
            "test1@google.com",
            "maria@test.com", 
            "pedro@test.com"
        ]
        
        # Contar usuarios de prueba antes de eliminar
        cur.execute("""
            SELECT COUNT(*) FROM usuarios 
            WHERE correo_electronico = ANY(%s)
        """, (test_emails,))
        
        count_before = cur.fetchone()[0]
        
        if count_before == 0:
            print("No se encontraron usuarios de prueba para eliminar.")
            return True
        
        # Mostrar usuarios que se van a eliminar
        cur.execute("""
            SELECT id, nombre, correo_electronico, rol 
            FROM usuarios 
            WHERE correo_electronico = ANY(%s)
            ORDER BY id
        """, (test_emails,))
        
        users_to_delete = cur.fetchall()
        print(f"\nUsuarios de prueba encontrados ({count_before}):")
        for user in users_to_delete:
            print(f"   ID: {user[0]}, Nombre: {user[1]}, Email: {user[2]}, Rol: {user[3]}")
        
        # Confirmar eliminación
        print(f"\n¿Estás seguro de que quieres eliminar {count_before} usuarios de prueba?")
        confirm = input("Escribe 'SI' para confirmar: ").strip().upper()
        
        if confirm != 'SI':
            print("Operación cancelada por el usuario.")
            return False
        
        # Eliminar usuarios de prueba
        cur.execute("""
            DELETE FROM usuarios 
            WHERE correo_electronico = ANY(%s)
        """, (test_emails,))
        
        deleted_count = cur.rowcount
        
        # Confirmar cambios
        conn.commit()
        
        print(f"Se eliminaron {deleted_count} usuarios de prueba correctamente.")
        
        # Verificar que se eliminaron
        cur.execute("""
            SELECT COUNT(*) FROM usuarios 
            WHERE correo_electronico = ANY(%s)
        """, (test_emails,))
        
        count_after = cur.fetchone()[0]
        
        if count_after == 0:
            print("Verificación: Todos los usuarios de prueba fueron eliminados.")
        else:
            print(f"Advertencia: Quedan {count_after} usuarios de prueba en la base de datos.")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error limpiando datos de prueba: {e}")
        return False

def clean_all_test_data():
    """Limpiar TODOS los datos de prueba (más agresivo)"""
    print("Limpiando TODOS los datos de prueba...")
    
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
            print("La tabla 'usuarios' no existe.")
            return False
        
        # Contar todos los usuarios
        cur.execute("SELECT COUNT(*) FROM usuarios")
        total_users = cur.fetchone()[0]
        
        if total_users == 0:
            print("No hay usuarios en la base de datos.")
            return True
        
        print(f"\nADVERTENCIA: Se van a eliminar TODOS los {total_users} usuarios de la base de datos.")
        print("Esta operación NO se puede deshacer.")
        
        # Confirmar eliminación
        confirm = input("Escribe 'ELIMINAR TODO' para confirmar: ").strip()
        
        if confirm != 'ELIMINAR TODO':
            print("Operación cancelada por el usuario.")
            return False
        
        # Eliminar todos los usuarios
        cur.execute("DELETE FROM usuarios")
        deleted_count = cur.rowcount
        
        # Confirmar cambios
        conn.commit()
        
        print(f"Se eliminaron {deleted_count} usuarios de la base de datos.")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error limpiando datos: {e}")
        return False

def show_test_users():
    """Mostrar usuarios de prueba actuales"""
    print("Mostrando usuarios de prueba actuales...")
    
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
            print("La tabla 'usuarios' no existe.")
            return False
        
        # Lista de emails de usuarios de prueba
        test_emails = [
            "test1@google.com",
            "maria@test.com", 
            "pedro@test.com"
        ]
        
        # Buscar usuarios de prueba
        cur.execute("""
            SELECT id, nombre, correo_electronico, rol, activo, fecha_registro
            FROM usuarios 
            WHERE correo_electronico = ANY(%s)
            ORDER BY id
        """, (test_emails,))
        
        users = cur.fetchall()
        
        if not users:
            print("No se encontraron usuarios de prueba.")
        else:
            print(f"\nUsuarios de prueba encontrados ({len(users)}):")
            print("-" * 80)
            for user in users:
                print(f"ID: {user[0]:<3} | Nombre: {user[1]:<15} | Email: {user[2]:<20} | Rol: {user[3]:<20} | Activo: {user[4]}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error mostrando usuarios: {e}")
        return False

def main():
    """Función principal"""
    print("🧹 Limpieza de datos de prueba - Auth Service")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "show":
            show_test_users()
        elif command == "clean":
            clean_test_data()
        elif command == "clean-all":
            clean_all_test_data()
        else:
            print("Comando no reconocido.")
            print("Comandos disponibles: show, clean, clean-all")
            return 1
    else:
        # Menú interactivo
        print("\nOpciones disponibles:")
        print("1. Mostrar usuarios de prueba actuales")
        print("2. Limpiar solo usuarios de prueba")
        print("3. Limpiar TODOS los usuarios (PELIGROSO)")
        print("4. Salir")
        
        while True:
            try:
                choice = input("\nSelecciona una opción (1-4): ").strip()
                
                if choice == "1":
                    show_test_users()
                    break
                elif choice == "2":
                    clean_test_data()
                    break
                elif choice == "3":
                    clean_all_test_data()
                    break
                elif choice == "4":
                    print("Saliendo...")
                    break
                else:
                    print("Opción inválida. Selecciona 1, 2, 3 o 4.")
            except KeyboardInterrupt:
                print("\nOperación cancelada.")
                break
    
    return 0

if __name__ == "__main__":
    exit(main())
