"""
Blueprint del CLIENTE — placeholder temporal.
Lo completaremos en el siguiente paso con su propio login y su dashboard/carrito.
"""
from flask import Blueprint

cliente_bp = Blueprint('cliente', __name__, url_prefix='/cliente')


@cliente_bp.route('/login')
def login():
    return "Login de cliente: próximo paso a construir."
