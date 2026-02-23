from sqlalchemy.orm import sessionmaker
from modelos import engine, Vehiculo

# Lista proporcionada por el usuario
vehiculos_data = [
    {"categoria": "CAMIONETAS", "nombre": "Eco 1 - L-200"},
    {"categoria": "CAMIONETAS", "nombre": "Eco 2 - HILUX"},
    {"categoria": "CAMIONETAS", "nombre": "Eco 3 - S-10 2025"},
    {"categoria": "CAMIONETAS", "nombre": "Eco 4 - RAM 700"},
    {"categoria": "CAMIONETAS", "nombre": "Eco 5 - SAVEIRO"},
    {"categoria": "CAMIONETAS", "nombre": "Eco 6 - TRANSIT"},
    {"categoria": "CAMIONETAS", "nombre": "Eco 7 - ESTACAS"},
    {"categoria": "CAMIONETAS", "nombre": "Eco 8 - S-10 2023"},
    {"categoria": "CAMIONETAS", "nombre": "Eco 9 - RAM PANADERA"},
    {"categoria": "CAMIONETAS", "nombre": "Eco 10 - RANGER"},
    {"categoria": "CAMIONETAS", "nombre": "Eco 11 - FRONTIER"},
    {"categoria": "GRÚAS", "nombre": "Eco 60 - FASSI"},
    {"categoria": "GRÚAS", "nombre": "Eco 20 - PM"},
    {"categoria": "GRÚAS", "nombre": "Eco 30 - HIAB"},
    {"categoria": "GRÚAS", "nombre": "Eco 40 - PETERBILT"},
    {"categoria": "GRÚAS", "nombre": "Eco 50 - WORKER"}
]

Session = sessionmaker(bind=engine)
session = Session()

print("Cargando vehículos...")

count = 0
for v in vehiculos_data:
    nombre = v["nombre"]
    categoria = v["categoria"]
    
    # Generar placa ficticia basada en el nombre (ej. Eco 1 -> ECO-001)
    placa_dummy = ""
    try:
        # Intentar extraer el número después de "Eco "
        start_idx = nombre.find("Eco ")
        if start_idx != -1:
            rest = nombre[start_idx + 4:] # "1 - L-200"
            num_str = rest.split(" ")[0] # "1"
            if num_str.isdigit():
                 placa_dummy = f"ECO-{int(num_str):03d}"
            else:
                 placa_dummy = f"GEN-{count:03d}"
        else:
             placa_dummy = f"GEN-{count:03d}"

    except Exception as e:
        print(f"Error generando placa para {nombre}: {e}")
        placa_dummy = f"ERR-{count:03d}"

    # Verificar si ya existe por placa
    existe = session.query(Vehiculo).filter_by(placas=placa_dummy).first()
    
    if not existe:
        nuevo_vehiculo = Vehiculo(
            modelo=f"{categoria}: {nombre}", # Guardamos categoría en el nombre para identificar mejor
            placas=placa_dummy,
            estado="Disponible"
        )
        session.add(nuevo_vehiculo)
        print(f"Agregado: {nombre} ({placa_dummy})")
    else:
        print(f"Saltado (ya existe placa {placa_dummy}): {nombre}")
    
    count += 1 # Incrementar siempre para backup ID

session.commit()
session.close()
print(f"Proceso terminado.")
