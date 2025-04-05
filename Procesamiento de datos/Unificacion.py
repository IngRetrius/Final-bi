import pandas as pd
import os
from pathlib import Path
import sys

def procesar_datos_jugadores_tres_torneos(ruta_csv_torneo1, ruta_csv_torneo2, ruta_csv_torneo3, ruta_salida='data/jugadores_unificados.csv'):
    """
    Procesa los datos de jugadores de tres torneos, combinando estadísticas 
    de jugadores duplicados y uniendo datos de los tres torneos.
    
    Args:
        ruta_csv_torneo1: Ruta al CSV con datos del torneo Apertura 2024A
        ruta_csv_torneo2: Ruta al CSV con datos del torneo Clausura 2024B
        ruta_csv_torneo3: Ruta al CSV con datos del torneo Apertura 2025A (actual)
        ruta_salida: Ruta donde se guardará el archivo CSV unificado
    """
    # Verificar que los archivos existen
    for ruta, nombre in zip(
        [ruta_csv_torneo1, ruta_csv_torneo2, ruta_csv_torneo3], 
        ["Apertura 2024A", "Clausura 2024B", "Apertura 2025A"]
    ):
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"No se pudo encontrar el archivo para el torneo {nombre} en la ruta: {ruta}")
    
    print("Cargando datos del torneo Apertura 2024A...")
    df_torneo1 = pd.read_csv(ruta_csv_torneo1)
    print(f"  ✓ Cargados {len(df_torneo1)} registros")
    
    print("Cargando datos del torneo Clausura 2024B...")
    df_torneo2 = pd.read_csv(ruta_csv_torneo2)
    print(f"  ✓ Cargados {len(df_torneo2)} registros")
    
    print("Cargando datos del torneo Apertura 2025A (actual)...")
    df_torneo3 = pd.read_csv(ruta_csv_torneo3)
    print(f"  ✓ Cargados {len(df_torneo3)} registros")
    
    # Agregar columna para identificar el torneo
    df_torneo1['Torneo'] = 'Apertura 2024A'
    df_torneo2['Torneo'] = 'Clausura 2024B'
    df_torneo3['Torneo'] = 'Apertura 2025A'
    
    # Combinar los tres DataFrames
    df_combinado = pd.concat([df_torneo1, df_torneo2, df_torneo3])
    print(f"Total de registros combinados: {len(df_combinado)}")
    
    # Procesar jugadores duplicados
    print("Procesando jugadores duplicados...")
    df_unificado = unificar_jugadores_duplicados(df_combinado)
    print(f"Total de registros unificados: {len(df_unificado)}")
    
    # Eliminar las columnas de posición y Sofascore Rating
    print("Eliminando columnas...")
    columnas_a_eliminar = ['Position', 'All_Positions', 'Average Sofascore Rating']
    for columna in columnas_a_eliminar:
        if columna in df_unificado.columns:
            df_unificado = df_unificado.drop(columna, axis=1)
            print(f"  ✓ Columna '{columna}' eliminada")
    
    # Ordenar primero por nombre y luego por torneo en orden específico
    print("Ordenando por nombre y torneo...")
    
    # Crear un mapeo para ordenar los torneos en el orden deseado
    torneo_orden = {
        'Apertura 2025A': 0,  # Primero
        'Clausura 2024B': 1,  # Segundo
        'Apertura 2024A': 2   # Tercero
    }
    
    # Crear una columna temporal para ordenar por torneo
    df_unificado['torneo_orden'] = df_unificado['Torneo'].map(torneo_orden)
    
    # Ordenar primero por nombre y luego por la columna temporal de orden de torneo
    df_unificado = df_unificado.sort_values(['Name', 'torneo_orden'])
    
    # Eliminar la columna temporal
    df_unificado = df_unificado.drop('torneo_orden', axis=1)
    
    # Crear directorio de salida si no existe
    ruta_salida_dir = os.path.dirname(ruta_salida)
    if ruta_salida_dir and not os.path.exists(ruta_salida_dir):
        os.makedirs(ruta_salida_dir, exist_ok=True)
    
    # Guardar como CSV 
    df_unificado.to_csv(ruta_salida, index=False)
    print(f"Datos unificados guardados en {ruta_salida}")
    
    return df_unificado

def unificar_jugadores_duplicados(df):
    """
    Unifica las estadísticas de jugadores duplicados.
    La estrategia es mantener los valores no-nulos de cada fila.
    No se incluyen las columnas de posición en el resultado final.
    """
    # Identificar columnas clave que identifican a un jugador único
    columnas_clave = ['Team', 'Name', 'Torneo']
    
    # Agrupar por nombre de jugador, equipo y torneo
    grupos = df.groupby(columnas_clave)
    
    # Lista para almacenar filas procesadas
    filas_procesadas = []
    
    # Procesar cada grupo (jugador)
    for nombre_grupo, grupo in grupos:
        # Inicializar fila unificada con valores no-nulos
        fila_unificada = {}
        
        # Copiar columnas clave
        for i, col in enumerate(columnas_clave):
            fila_unificada[col] = nombre_grupo[i]
        
        # Para cada columna estadística, tomar el primer valor no-nulo
        for columna in df.columns:
            if columna not in columnas_clave and columna != 'Position':
                # Obtener valores no nulos
                valores_no_nulos = grupo[columna].dropna()
                if not valores_no_nulos.empty:
                    fila_unificada[columna] = valores_no_nulos.iloc[0]
                else:
                    fila_unificada[columna] = None
        
        filas_procesadas.append(fila_unificada)
    
    # Crear DataFrame con filas procesadas
    df_procesado = pd.DataFrame(filas_procesadas)
    
    return df_procesado

# Ejemplo de uso
if __name__ == "__main__":
    # Definir ruta de salida predeterminada
    ruta_salida = "data/jugadores_unificados.csv"
    
    # Obtener la ruta base del proyecto - ajusta esto según tu estructura de directorios
    # Esto asume que estás ejecutando el script desde el directorio 'Procesamiento de datos'
    base_path = os.path.join("..", "scraper", "data")
    
    # Rutas a los archivos CSV - ajústalas según la ubicación real de tus archivos
    ruta_csv_torneo1 = os.path.join(base_path, "apertura_57374", "all", "jugadores_liga_colombiana_completo.csv")
    ruta_csv_torneo2 = os.path.join(base_path, "clausura_63819", "all", "jugadores_liga_colombiana_completo.csv")
    ruta_csv_torneo3 = os.path.join(base_path, "apertura_70681", "all", "jugadores_liga_colombiana_completo.csv")
    
    print("Rutas de archivos a procesar:")
    print(f"Torneo 1: {ruta_csv_torneo1}")
    print(f"Torneo 2: {ruta_csv_torneo2}")
    print(f"Torneo 3: {ruta_csv_torneo3}")
    
    # Verificar si los archivos existen
    archivos_existen = True
    for ruta, nombre in zip(
        [ruta_csv_torneo1, ruta_csv_torneo2, ruta_csv_torneo3], 
        ["Apertura 2024A", "Clausura 2024B", "Apertura 2025A"]
    ):
        if not os.path.exists(ruta):
            print(f"ERROR: No se encontró el archivo para el torneo {nombre} en: {ruta}")
            archivos_existen = False
    
    if not archivos_existen:
        print("\nPor favor, especifica las rutas correctas cuando ejecutes el script:")
        print("python Unificacion.py <ruta_torneo1> <ruta_torneo2> <ruta_torneo3> [ruta_salida]")
        
        # Si hay argumentos de línea de comandos, usarlos como rutas
        if len(sys.argv) >= 4:
            ruta_csv_torneo1 = sys.argv[1]
            ruta_csv_torneo2 = sys.argv[2]
            ruta_csv_torneo3 = sys.argv[3]
            if len(sys.argv) >= 5:
                ruta_salida = sys.argv[4]
            print("\nUsando rutas desde argumentos de línea de comandos.")
        else:
            # Solicitar rutas al usuario
            print("\nPor favor, ingresa las rutas completas a los archivos:")
            ruta_csv_torneo1 = input("Ruta al CSV del torneo Apertura 2024A: ")
            ruta_csv_torneo2 = input("Ruta al CSV del torneo Clausura 2024B: ")
            ruta_csv_torneo3 = input("Ruta al CSV del torneo Apertura 2025A: ")
            ruta_salida_input = input("Ruta de salida para el CSV unificado (deja en blanco para usar 'data/jugadores_unificados.csv'): ")
            if ruta_salida_input:
                ruta_salida = ruta_salida_input
    
    try:
        # Procesar datos
        df_unificado = procesar_datos_jugadores_tres_torneos(
            ruta_csv_torneo1, 
            ruta_csv_torneo2, 
            ruta_csv_torneo3,
            ruta_salida
        )
        
        print("\nProceso completado. El archivo CSV unificado está listo para su análisis posterior.")
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print("No se pudo completar el procesamiento de datos.")