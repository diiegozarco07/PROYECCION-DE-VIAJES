import hashlib
import os

# Simulación de base de datos de usuarios (en producción usar DB real)
# En un caso real, las contraseñas estarían hasheadas.
USERS = {
    "admin": {
        "password": "admin123", # Cambiar por os.getenv("ADMIN_PASSWORD")
        "role": "Admin",
        "name": "Administrador Principal"
    },
    "trabajador": {
        "password": "user123",
        "role": "Trabajador",
        "name": "Usuario Operativo"
    }
}

def verify_login(username, password):
    if username in USERS:
        if USERS[username]["password"] == password:
            return USERS[username]
    return None
