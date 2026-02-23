import hashlib
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env si existe
load_dotenv()

# Simulación de base de datos de usuarios (en producción usar DB real)
# En un caso real, las contraseñas estarían hasheadas.
USERS = {
    "admin": {
        "password": os.getenv("ADMIN_PASSWORD"),
        "role": "Admin",
        "name": "Administrador Principal"
    },
    "trabajador": {
        "password": os.getenv("USER_PASSWORD"),
        "role": "Trabajador",
        "name": "Usuario Operativo"
    }
}

def verify_login(username, password):
    if username in USERS:
        # Verificar que la contraseña en la configuración no sea None
        stored_password = USERS[username]["password"]
        if stored_password and stored_password == password:
            return USERS[username]
    return None
