import os
from flask import Flask, redirect, url_for
from dotenv import load_dotenv

from routes.administrador import admin_bp
from routes import catalogo  # registra las rutas de categorías/marcas/productos en admin_bp
from routes.cliente import cliente_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave-temporal-cambiar')

# Cada perfil tiene su propio módulo, con su propio login y sus propias vistas
app.register_blueprint(admin_bp)
app.register_blueprint(cliente_bp)


@app.route('/')
def inicio():
    # Página raíz temporal: por ahora manda directo al login de administrador.
    # Cuando armemos la tienda pública, aquí irá el catálogo general.
    return redirect(url_for('admin.login'))


if __name__ == '__main__':
    app.run(debug=True)
