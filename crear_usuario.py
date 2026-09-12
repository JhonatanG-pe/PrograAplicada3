"""
Script interactivo para crear un usuario real en la base de datos.
Sirve tanto para crear Administradores como Clientes.

Ejecutar con: python crear_usuario.py
"""
from datetime import datetime
from werkzeug.security import generate_password_hash
from db import obtener_conexion


def elegir_perfil(cursor):
    cursor.execute("SELECT IdPerfil, Nombre FROM Perfiles WHERE EstadoRegistro = 1 ORDER BY Nombre")
    perfiles = cursor.fetchall()

    if not perfiles:
        print("No hay perfiles registrados todavía. Primero inserta 'Administrador' y 'Cliente' en la tabla Perfiles.")
        raise SystemExit

    print("\nPerfiles disponibles:")
    for fila in perfiles:
        print(f"  {fila.IdPerfil} - {fila.Nombre}")

    id_elegido = int(input("Ingresa el IdPerfil que quieres asignar a este usuario: "))
    return id_elegido


def main():
    print("=== Crear nuevo usuario ===\n")
    dni = input("DNI: ").strip()
    nombres = input("Nombres: ").strip()
    apellido_paterno = input("Apellido paterno: ").strip()
    apellido_materno = input("Apellido materno (Enter para omitir): ").strip() or None
    celular = input("Celular (Enter para omitir): ").strip() or None
    correo = input("Correo electrónico: ").strip()
    clave_texto_plano = input("Contraseña: ").strip()

    clave_hash = generate_password_hash(clave_texto_plano)

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    id_perfil = elegir_perfil(cursor)

    cursor.execute(
        """
        INSERT INTO Usuario (DNI, Nombres, ApellidoPaterno, ApellidoMaterno, Celular,
                              CorreoElectronico, Clave, FechaCreacion, EstadoRegistro)
        OUTPUT INSERTED.IdUsuario
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        dni, nombres, apellido_paterno, apellido_materno, celular, correo, clave_hash, datetime.now(),
    )
    id_usuario = cursor.fetchone()[0]

    cursor.execute(
        "INSERT INTO Usuario_Perfiles (IdUsuario, IdPerfil, EstadoRegistro) VALUES (?, ?, 1)",
        id_usuario, id_perfil,
    )

    conexion.commit()
    conexion.close()

    print(f"\n✅ Usuario creado correctamente. IdUsuario = {id_usuario}")
    print(f"   Ahora puedes iniciar sesión con el correo '{correo}' y la contraseña que ingresaste.")


if __name__ == '__main__':
    main()
