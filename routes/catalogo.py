"""
Módulo de catálogo: Categorías, Marcas y Productos.
Estas rutas se agregan al mismo Blueprint 'admin' (prefijo /admin),
así que comparten el login y la protección de administrador.py.
"""
from flask import render_template, request, redirect, url_for, flash, session
from db import obtener_conexion
from routes.administrador import admin_bp, admin_requerido


# ==========================================================================
# CATEGORÍAS
# ==========================================================================
@admin_bp.route('/categorias')
@admin_requerido
def lista_categorias():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT IdCategoria, Descripcion, Activo FROM Categoria ORDER BY Descripcion")
    categorias = cursor.fetchall()
    conexion.close()
    return render_template('admin/categorias.html', categorias=categorias)


@admin_bp.route('/categorias/nueva', methods=['GET', 'POST'])
@admin_requerido
def nueva_categoria():
    if request.method == 'POST':
        descripcion = request.form.get('descripcion', '').strip()
        if not descripcion:
            flash('La descripción es obligatoria.', 'error')
            return render_template('admin/categoria_form.html', categoria=None)

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO Categoria (Descripcion, Activo) VALUES (?, 1)", descripcion)
        conexion.commit()
        conexion.close()
        flash('Categoría creada correctamente.', 'success')
        return redirect(url_for('admin.lista_categorias'))

    return render_template('admin/categoria_form.html', categoria=None)


@admin_bp.route('/categorias/editar/<int:id_categoria>', methods=['GET', 'POST'])
@admin_requerido
def editar_categoria(id_categoria):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    if request.method == 'POST':
        descripcion = request.form.get('descripcion', '').strip()
        activo = 1 if request.form.get('activo') == 'on' else 0
        cursor.execute(
            "UPDATE Categoria SET Descripcion = ?, Activo = ? WHERE IdCategoria = ?",
            descripcion, activo, id_categoria,
        )
        conexion.commit()
        conexion.close()
        flash('Categoría actualizada.', 'success')
        return redirect(url_for('admin.lista_categorias'))

    cursor.execute("SELECT IdCategoria, Descripcion, Activo FROM Categoria WHERE IdCategoria = ?", id_categoria)
    categoria = cursor.fetchone()
    conexion.close()
    return render_template('admin/categoria_form.html', categoria=categoria)


# ==========================================================================
# MARCAS (mismo patrón que Categorías)
# ==========================================================================
@admin_bp.route('/marcas')
@admin_requerido
def lista_marcas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT IdMarca, Descripcion, Activo FROM Marca ORDER BY Descripcion")
    marcas = cursor.fetchall()
    conexion.close()
    return render_template('admin/marcas.html', marcas=marcas)


@admin_bp.route('/marcas/nueva', methods=['GET', 'POST'])
@admin_requerido
def nueva_marca():
    if request.method == 'POST':
        descripcion = request.form.get('descripcion', '').strip()
        if not descripcion:
            flash('La descripción es obligatoria.', 'error')
            return render_template('admin/marca_form.html', marca=None)

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO Marca (Descripcion, Activo) VALUES (?, 1)", descripcion)
        conexion.commit()
        conexion.close()
        flash('Marca creada correctamente.', 'success')
        return redirect(url_for('admin.lista_marcas'))

    return render_template('admin/marca_form.html', marca=None)


@admin_bp.route('/marcas/editar/<int:id_marca>', methods=['GET', 'POST'])
@admin_requerido
def editar_marca(id_marca):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    if request.method == 'POST':
        descripcion = request.form.get('descripcion', '').strip()
        activo = 1 if request.form.get('activo') == 'on' else 0
        cursor.execute(
            "UPDATE Marca SET Descripcion = ?, Activo = ? WHERE IdMarca = ?",
            descripcion, activo, id_marca,
        )
        conexion.commit()
        conexion.close()
        flash('Marca actualizada.', 'success')
        return redirect(url_for('admin.lista_marcas'))

    cursor.execute("SELECT IdMarca, Descripcion, Activo FROM Marca WHERE IdMarca = ?", id_marca)
    marca = cursor.fetchone()
    conexion.close()
    return render_template('admin/marca_form.html', marca=marca)


# ==========================================================================
# PRODUCTOS
# ==========================================================================
@admin_bp.route('/productos')
@admin_requerido
def lista_productos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT p.IdProducto, p.Nombre, c.Descripcion AS Categoria, m.Descripcion AS Marca,
               p.Precio, p.Stock, p.StockMinimo, p.Activo
        FROM Producto p
        LEFT JOIN Categoria c ON c.IdCategoria = p.IdCategoria
        LEFT JOIN Marca m ON m.IdMarca = p.IdMarca
        ORDER BY p.Nombre
        """
    )
    productos = cursor.fetchall()
    conexion.close()
    return render_template('admin/productos.html', productos=productos)


@admin_bp.route('/productos/nuevo', methods=['GET', 'POST'])
@admin_requerido
def nuevo_producto():
    categorias, marcas = _obtener_categorias_marcas_activas()

    if request.method == 'POST':
        datos = _leer_formulario_producto()
        if datos is None:
            return render_template('admin/producto_form.html', producto=None,
                                    categorias=categorias, marcas=marcas)

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO Producto (Nombre, Descripcion, IdCategoria, IdMarca, Precio,
                                   Stock, StockMinimo, Activo, IdUsuario)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            datos['nombre'], datos['descripcion'], datos['id_categoria'], datos['id_marca'],
            datos['precio'], datos['stock'], datos['stock_minimo'], session['id_usuario'],
        )
        conexion.commit()
        conexion.close()
        flash('Producto creado correctamente.', 'success')
        return redirect(url_for('admin.lista_productos'))

    return render_template('admin/producto_form.html', producto=None, categorias=categorias, marcas=marcas)


@admin_bp.route('/productos/editar/<int:id_producto>', methods=['GET', 'POST'])
@admin_requerido
def editar_producto(id_producto):
    categorias, marcas = _obtener_categorias_marcas_activas()
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    if request.method == 'POST':
        datos = _leer_formulario_producto()
        if datos is None:
            conexion.close()
            return render_template('admin/producto_form.html', producto=None,
                                    categorias=categorias, marcas=marcas)

        activo = 1 if request.form.get('activo') == 'on' else 0
        cursor.execute(
            """
            UPDATE Producto
            SET Nombre = ?, Descripcion = ?, IdCategoria = ?, IdMarca = ?,
                Precio = ?, Stock = ?, StockMinimo = ?, Activo = ?
            WHERE IdProducto = ?
            """,
            datos['nombre'], datos['descripcion'], datos['id_categoria'], datos['id_marca'],
            datos['precio'], datos['stock'], datos['stock_minimo'], activo, id_producto,
        )
        conexion.commit()
        conexion.close()
        flash('Producto actualizado.', 'success')
        return redirect(url_for('admin.lista_productos'))

    cursor.execute(
        """
        SELECT IdProducto, Nombre, Descripcion, IdCategoria, IdMarca,
               Precio, Stock, StockMinimo, Activo
        FROM Producto WHERE IdProducto = ?
        """,
        id_producto,
    )
    producto = cursor.fetchone()
    conexion.close()
    return render_template('admin/producto_form.html', producto=producto, categorias=categorias, marcas=marcas)


def _obtener_categorias_marcas_activas():
    """Trae categorías y marcas activas, para llenar los <select> del formulario."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT IdCategoria, Descripcion FROM Categoria WHERE Activo = 1 ORDER BY Descripcion")
    categorias = cursor.fetchall()
    cursor.execute("SELECT IdMarca, Descripcion FROM Marca WHERE Activo = 1 ORDER BY Descripcion")
    marcas = cursor.fetchall()
    conexion.close()
    return categorias, marcas


def _leer_formulario_producto():
    """Lee y valida los campos del formulario de producto. Devuelve None si falta algo obligatorio."""
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    id_categoria = request.form.get('id_categoria') or None
    id_marca = request.form.get('id_marca') or None
    precio = request.form.get('precio', '').strip()
    stock = request.form.get('stock', '0').strip()
    stock_minimo = request.form.get('stock_minimo', '5').strip()

    if not nombre or not precio:
        flash('Nombre y precio son obligatorios.', 'error')
        return None

    try:
        precio = float(precio)
        stock = int(stock or 0)
        stock_minimo = int(stock_minimo or 5)
    except ValueError:
        flash('Precio y stock deben ser números válidos.', 'error')
        return None

    return {
        'nombre': nombre,
        'descripcion': descripcion,
        'id_categoria': int(id_categoria) if id_categoria else None,
        'id_marca': int(id_marca) if id_marca else None,
        'precio': precio,
        'stock': stock,
        'stock_minimo': stock_minimo,
    }
