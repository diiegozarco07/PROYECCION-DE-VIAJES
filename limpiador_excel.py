import pandas as pd
import unicodedata
from datetime import datetime

def limpiar_texto(texto):
    """
    Función auxiliar para limpiar texto:
    - Convierte a minúsculas
    - Elimina espacios al inicio y final
    - Elimina acentos
    """
    if not isinstance(texto, str):
        return str(texto) if pd.notna(texto) else ""
    
    texto = texto.lower().strip()
    # Eliminar acentos
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                    if unicodedata.category(c) != 'Mn')
    return texto

def procesar_excel(ruta_archivo):
    """
    Lee un archivo Excel, limpia los datos y retorna una lista de diccionarios.
    
    Args:
        ruta_archivo (str): Ruta al archivo Excel.
        
    Returns:
        list[dict]: Lista de diccionarios con los datos limpios.
        
    Raises:
        ValueError: Si hay inconsistencias en las fechas o destinos no reconocidos.
        Exception: Para otros errores generales.
    """
    try:
        # Cargar el Excel ignorando las primeras 5 filas (header=5 significa que la fila 6 es el encabezado)
        df = pd.read_excel(ruta_archivo, header=5)
        
        # Mapa de columnas: Nombre en Excel -> Nombre en nuestro diccionario de salida
        mapa_columnas = {
            'De dónde parte': 'origen',
            'A dónde va': 'destino',
            'Personal a cargo de actividad': 'personal',
            'F inicial': 'fecha_inicio',
            'F final': 'fecha_fin',
            'Vehículo': 'vehiculo'
        }
        
        # Verificar que las columnas requeridas existan en el DataFrame
        # Nota: Pandas a veces agrega espacios o caracteres raros en los headers si el Excel está sucio
        # Una práctica robusta sería limpiar también los nombres de columnas, pero aquí asumimos exactitud.
        columnas_faltantes = [col for col in mapa_columnas.keys() if col not in df.columns]
        if columnas_faltantes:
            raise ValueError(f"El archivo no contiene las columnas requeridas: {columnas_faltantes}")
            
        # Filtrar solo las columnas que nos interesan y renombrarlas
        df = df[list(mapa_columnas.keys())].rename(columns=mapa_columnas)
        
        # Diccionario de equivalencias para destinos (ya normalizados sin acentos y en minúsculas)
        # Nota: Las claves deben coincidir con el texto después de pasar por limpiar_texto()
        equivalencias_destino = {
            'qro': 'Querétaro',
            'qro.': 'Querétaro',
            'queretaro': 'Querétaro',
            'santiago de queretaro': 'Querétaro',
            'micho': 'Morelia',
            'michoacan': 'Morelia',
            'morelia': 'Morelia'
        }
        
        datos_limpios = []
        
        # Iterar sobre las filas del DataFrame
        for index, row in df.iterrows():
            # Si la fila está vacía en campos clave, saltar (o manejar según necesidad)
            # Aquí asumimos que si no hay fechas, la fila no es válida para un viaje
            if pd.isna(row['fecha_inicio']) or pd.isna(row['fecha_fin']):
                continue

            fila_limpia = {}
            
            # 1. Limpieza de textos y Mapeo a claves de Base de Datos (modelos.py)
            
            # Origen (No está explícitamente en el modelo Viaje, pero asumiremos que es parte del proyecto o se ignora, 
            # pero el usuario pidió extraerla. La guardaremos con clave 'origen' por si acaso)
            # Nota: El modelo Viaje tiene 'destino_limpio', 'personal_asignado', etc.
            
            # 'De dónde parte' -> origen (temporal)
            fila_limpia['origen'] = limpiar_texto(row['origen'])

            # 'A dónde va' -> destino_limpio
            destino_crudo = limpiar_texto(row['destino'])
            if destino_crudo in equivalencias_destino:
                fila_limpia['destino_limpio'] = equivalencias_destino[destino_crudo]
            else:
                 # Si el destino no está en el diccionario, lanzar excepción y detener todo
                raise ValueError(f"Error en fila {index + 7}: Destino '{destino_crudo}' no reconocido en el diccionario de equivalencias.")
            
            # 'Personal a cargo de actividad' -> personal_asignado
            fila_limpia['personal_asignado'] = limpiar_texto(row['personal'])
            
            # 'Vehículo' -> vehiculo_nombre (temporal, pues el modelo pide ID, no nombre string)
            fila_limpia['vehiculo_nombre'] = limpiar_texto(row['vehiculo'])

            # 2. Conversión y Validación de Fechas
            try:
                f_inicio = pd.to_datetime(row['fecha_inicio']).date()
                f_fin = pd.to_datetime(row['fecha_fin']).date()
                
                # 'F inicial' -> fecha_inicio
                fila_limpia['fecha_inicio'] = f_inicio
                # 'F final' -> fecha_fin
                fila_limpia['fecha_fin'] = f_fin
                
            except Exception as e:
                raise ValueError(f"Error en fila {index + 7}: Formato de fecha inválido. {e}")
            
            # Regla estricta: F final < F inicial
            if f_fin < f_inicio:
                raise ValueError(f"Error en fila {index + 7}: La fecha final ({f_fin}) es menor que la inicial ({f_inicio}).")
            
            datos_limpios.append(fila_limpia)
            
        return datos_limpios

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo en {ruta_archivo}")
        return []
    except Exception as e:
        print(f"Error procesando el archivo: {e}")
        raise e

# Ejemplo de uso (comentado para que no se ejecute al importar)
# if __name__ == "__main__":
#     try:
#         datos = procesar_excel("ruta/a/tu/archivo.xlsx")
#         for d in datos:
#             print(d)
#     except Exception as e:
#         print(e)
