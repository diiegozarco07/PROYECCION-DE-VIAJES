from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import date

# 1. Configuración de la Base de Datos
# Usamos SQLite local para pruebas como se solicitó.
# El archivo de la base de datos se llamará 'logistica.db'.
DATABASE_URL = "sqlite:///logistica.db"

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL, echo=True)  # echo=True para ver las consultas SQL en consola

# Clase base para nuestros modelos
Base = declarative_base()

# 2. Definición de Modelos

class Usuario(Base):
    """
    Modelo para la tabla Usuarios.
    Almacena la información del personal (Admins y Trabajadores).
    """
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_completo = Column(String, nullable=False)
    correo_google = Column(String, unique=True, nullable=False)
    rol = Column(String, nullable=False)  # Esperado: 'Admin' o 'Trabajador'
    activo = Column(Boolean, default=True)

    # Relaciones (opcional pero recomendado para facilitar consultas)
    viajes_creados = relationship("Viaje", back_populates="creador")

    def __repr__(self):
        return f"<Usuario(id={self.id}, nombre='{self.nombre_completo}', rol='{self.rol}')>"


class Vehiculo(Base):
    """
    Modelo para la tabla Vehiculos.
    Gestiona la flota disponible para los viajes.
    """
    __tablename__ = 'vehiculos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    modelo = Column(String, nullable=False)
    placas = Column(String, unique=True, nullable=False)
    estado = Column(String, nullable=False)  # Ej: 'Disponible', 'En Mantenimiento', 'En Uso'

    # Relaciones
    viajes = relationship("Viaje", back_populates="vehiculo")

    def __repr__(self):
        return f"<Vehiculo(id={self.id}, modelo='{self.modelo}', placas='{self.placas}')>"


class Viaje(Base):
    """
    Modelo para la tabla Viajes.
    Registra los detalles de logística, costos y asignaciones.
    """
    __tablename__ = 'viajes'

    id_viaje = Column(Integer, primary_key=True, autoincrement=True)
    
    # Claves foráneas
    creador_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    vehiculo_id = Column(Integer, ForeignKey('vehiculos.id'), nullable=True) # Puede ser nulo si aún no se asigna
    
    # Detalles del proyecto
    proyecto = Column(String, nullable=False)
    destino_limpio = Column(String, nullable=False)
    personal_asignado = Column(String, nullable=False) # Podría ser un JSON o texto separado por comas
    
    # Fechas
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    
    # Estado del viaje
    estado_viaje = Column(String, default='Pendiente de Asignación')
    
    # Costos (Floats y permitiendo nulos como se especificó)
    costo_toka = Column(Float, nullable=True)
    costo_casetas = Column(Float, nullable=True)
    costo_hospedaje = Column(Float, nullable=True)
    
    # Integración externa
    id_calendario_google = Column(String, nullable=True)
    
    # Nuevos campos solicitados
    breve_descripcion = Column(String, nullable=True) # Descripción detallada de logística
    observaciones_vehiculo = Column(String, nullable=True) # Qué vehículos o grúas necesita
    
    # Notificaciones
    correo_trabajador = Column(String, nullable=False) # Correo para invitaciones de Calendar

    # Relaciones
    creador = relationship("Usuario", back_populates="viajes_creados")
    vehiculo = relationship("Vehiculo", back_populates="viajes")

    def __repr__(self):
        return f"<Viaje(id={self.id_viaje}, destino='{self.destino_limpio}', estado='{self.estado_viaje}')>"


# 3. Lógica de creación de tablas
def inicializar_db():
    """
    Crea todas las tablas definidas en los modelos si no existen.
    Esta función debe ejecutarse al inicio de la aplicación.
    """
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(engine)
    print("Tablas creadas exitosamente.")

if __name__ == "__main__":
    # Si este script se ejecuta directamente, inicializa la base de datos
    inicializar_db()

    # Bloque de prueba opcional para verificar la conexión
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Conexión a base de datos establecida y sesión creada.")
    session.close()
