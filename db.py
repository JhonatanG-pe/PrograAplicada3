"""
Módulo centralizado de conexión a SQL Server.
Todas las consultas del sistema pasan por aquí, para no repetir
la cadena de conexión en cada archivo.
"""
import os
import pyodbc
from dotenv import load_dotenv

# Carga las variables del archivo .env (DB_SERVER, DB_NAME, etc.)
load_dotenv()


def obtener_conexion():
    """Abre y devuelve una nueva conexión a la base de datos 'ventas'."""
    cadena_conexion = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={os.environ['DB_SERVER']};"
        f"DATABASE={os.environ['DB_NAME']};"
        f"UID={os.environ['DB_USER']};"
        f"PWD={os.environ['DB_PASSWORD']}"
    )
    return pyodbc.connect(cadena_conexion)
