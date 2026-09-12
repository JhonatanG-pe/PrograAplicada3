"""
Módulo de seguridad para el ADMINISTRADOR.
Tiene su propio formulario de login (no comparte pantalla con el cliente).
Aun así, siempre se valida en el servidor que el usuario tenga
realmente el perfil 'Administrador' en Usuario_Perfiles antes de dejarlo entrar.
"""
from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from db import obtener_conexion

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_requerido(vista):
    """Protege una vista: solo deja pasar si hay sesión activa de Administrador."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if session.get('nombre_perfil') != 'Administrador':
            return redirect(url_for('admin.login'))
        return vista(*args, **kwargs)
    return envoltura


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        clave_ingresada = request.form.get('clave', '')

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT IdUsuario, Nombres, ApellidoPaterno, Clave, EstadoRegistro
            FROM Usuario
            WHERE CorreoElectronico = ?
            """,
            correo,
        )
        fila = cursor.fetchone()

        # Caso 1: no existe ese correo
        if fila is None:
            conexion.close()
            flash('Correo o contraseña incorrectos.', 'error')
            return render_template('admin/login.html')

        id_usuario, nombres, apellido_paterno, clave_guardada, estado_registro = fila

        # Caso 2: usuario inactivo
        if not estado_registro:
            conexion.close()
            flash('Este usuario está inactivo.', 'error')
            return render_template('admin/login.html')

        # Caso 3: contraseña incorrecta
        if not check_password_hash(clave_guardada, clave_ingresada):
            conexion.close()
            flash('Correo o contraseña incorrectos.', 'error')
            return render_template('admin/login.html')

        # Caso 4 (clave de seguridad): ¿este usuario tiene REALMENTE
        # el perfil Administrador asignado? No importa si adivinó
        # la contraseña de un cliente, sin este perfil no entra aquí.
        cursor.execute(
            """
            SELECT 1
            FROM Usuario_Perfiles up
            INNER JOIN Perfiles p ON p.IdPerfil = up.IdPerfil
            WHERE up.IdUsuario = ? AND p.Nombre = 'Administrador'
                  AND up.EstadoRegistro = 1 AND p.EstadoRegistro = 1
            """,
            id_usuario,
        )
        tiene_perfil_admin = cursor.fetchone()
        conexion.close()

        if tiene_perfil_admin is None:
            flash('Este usuario no tiene perfil de Administrador.', 'error')
            return render_template('admin/login.html')

        # Todo correcto: creamos la sesión de administrador
        session.clear()
        session['id_usuario'] = id_usuario
        session['nombre_completo'] = f"{nombres} {apellido_paterno}"
        session['nombre_perfil'] = 'Administrador'
        cargar_menu_admin(id_usuario)

        return redirect(url_for('admin.panel'))

    return render_template('admin/login.html')


def cargar_menu_admin(id_usuario):
    """Carga en sesión las opciones de menú (OpcionesMenu) del perfil Administrador."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT om.IdOpcionMenu, om.Nombre, om.UrlMenu
        FROM OpcionesMenu_Perfiles omp
        INNER JOIN OpcionesMenu om ON om.IdOpcionMenu = omp.IdOpcionMenu
        INNER JOIN Perfiles p ON p.IdPerfil = omp.IdPerfil
        WHERE p.Nombre = 'Administrador' AND omp.EstadoRegistro = 1
              AND om.EstadoRegistro = 1 AND om.IdPadre IS NULL
        ORDER BY omp.Orden
        """
    )
    session['menu'] = [
        {'id': fila[0], 'nombre': fila[1], 'url': fila[2]}
        for fila in cursor.fetchall()
    ]
    conexion.close()


@admin_bp.route('/')
@admin_requerido
def panel():
    return render_template('admin/panel.html')


@admin_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))


@admin_bp.route('/usuarios')
@admin_requerido
def lista_usuarios():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT u.IdUsuario, u.Nombres, u.ApellidoPaterno, u.CorreoElectronico,
               u.EstadoRegistro, STRING_AGG(p.Nombre, ', ') AS Perfiles
        FROM Usuario u
        LEFT JOIN Usuario_Perfiles up ON up.IdUsuario = u.IdUsuario AND up.EstadoRegistro = 1
        LEFT JOIN Perfiles p ON p.IdPerfil = up.IdPerfil
        GROUP BY u.IdUsuario, u.Nombres, u.ApellidoPaterno, u.CorreoElectronico, u.EstadoRegistro
        ORDER BY u.Nombres
        """
    )
    usuarios = cursor.fetchall()
    conexion.close()
    return render_template('admin/usuarios.html', usuarios=usuarios)


@admin_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@admin_requerido
def nuevo_usuario():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT IdPerfil, Nombre FROM Perfiles WHERE EstadoRegistro = 1 ORDER BY Nombre")
    perfiles = [{'id': fila.IdPerfil, 'nombre': fila.Nombre} for fila in cursor.fetchall()]

    if request.method == 'POST':
        dni = request.form.get('dni', '').strip()
        nombres = request.form.get('nombres', '').strip()
        apellido_paterno = request.form.get('apellido_paterno', '').strip()
        apellido_materno = request.form.get('apellido_materno', '').strip() or None
        celular = request.form.get('celular', '').strip() or None
        correo = request.form.get('correo', '').strip()
        clave = request.form.get('clave', '')
        id_perfil = request.form.get('id_perfil', '')

        campos_obligatorios = (dni, nombres, apellido_paterno, correo, clave, id_perfil)
        if not all(campos_obligatorios):
            conexion.close()
            flash('Completa todos los campos obligatorios.', 'error')
            return render_template('admin/usuario_form.html', perfiles=perfiles)

        clave_hash = generate_password_hash(clave)
        try:
            cursor.execute(
                """
                INSERT INTO Usuario (DNI, Nombres, ApellidoPaterno, ApellidoMaterno, Celular,
                                      CorreoElectronico, Clave, UsuarioCreacion, FechaCreacion, EstadoRegistro)
                OUTPUT INSERTED.IdUsuario
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                dni, nombres, apellido_paterno, apellido_materno, celular,
                correo, clave_hash, session['id_usuario'], datetime.now(),
            )
            id_usuario_nuevo = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO Usuario_Perfiles (IdUsuario, IdPerfil, EstadoRegistro) VALUES (?, ?, 1)",
                id_usuario_nuevo, int(id_perfil),
            )
            conexion.commit()
            conexion.close()
            flash('Usuario creado correctamente.', 'success')
            return redirect(url_for('admin.lista_usuarios'))
        except Exception as error:
            conexion.rollback()
            conexion.close()
            flash(f'No se pudo crear el usuario: {error}', 'error')
            return render_template('admin/usuario_form.html', perfiles=perfiles)

    conexion.close()
    return render_template('admin/usuario_form.html', perfiles=perfiles)
