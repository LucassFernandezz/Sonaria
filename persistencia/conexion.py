import mysql.connector
from mysql.connector import Error

CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "tu_password",
    "database": "sonaria",
    "port": 3306
}

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host=CONFIG["host"],
            user=CONFIG["user"],
            password=CONFIG["password"],
            database=CONFIG["database"],
            port=CONFIG["port"]
        )
        return conexion

    except Error as e:
        print("Error conectando a MySQL:", e)
        return None