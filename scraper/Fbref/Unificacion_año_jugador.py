import pandas as pd
import os
import re
import datetime

# Lista de columnas esperadas en el nuevo formato
COLUMNAS_ESPERADAS = [
    "partido", "Fecha", "Día de la semana", "Competición", "Ronda o Fase", 
    "Sede", "Resultado", "Equipo", "Oponente", "Titular", "Posición", 
    "Minutos", "Goles", "Asistencias", "Penales marcados", "Penales intentados", 
    "Tiros totales", "Tiros a puerta", "Tarjetas amarillas", "Tarjetas rojas", 
    "Faltas cometidas", "Faltas recibidas", "Fuera de juego", "Centros", 
    "Entradas ganadas", "Intercepciones", "Goles en propia", "Penales ganados", 
    "Penales concedidos"
]

# Mapeo opcional de nombres de columnas antiguos a nuevos
MAPEO_COLUMNAS = {
    "Date": "Fecha",
    "Day": "Día de la semana",
    "Comp": "Competición",
    "Round": "Ronda o Fase",
    "Venue": "Sede",
    "Result": "Resultado",
    "Squad": "Equipo",
    "Opponent": "Oponente",
    "Start": "Titular",
    "Pos": "Posición",
    "Min": "Minutos",
    "Gls": "Goles",
    "Ast": "Asistencias",
    "PK": "Penales marcados",
    "PKatt": "Penales intentados",
    "Sh": "Tiros totales",
    "SoT": "Tiros a puerta",
    "CrdY": "Tarjetas amarillas",
    "CrdR": "Tarjetas rojas",
    "Fls": "Faltas cometidas",
    "Fld": "Faltas recibidas",
    "Off": "Fuera de juego",
    "Crs": "Centros",
    "TklW": "Entradas ganadas",
    "Int": "Intercepciones",
    "OG": "Goles en propia",
    "PKwon": "Penales ganados",
    "PKcon": "Penales concedidos"
}

def extraer_informacion_archivo(nombre_archivo):
    """
    Extrae el año y el nombre del jugador del nombre del archivo.
    El formato esperado es: YYYY_NombreJugador.csv
    """
    # Extraer el año usando una expresión regular
    año_match = re.search(r'(\d{4})_', nombre_archivo)
    if año_match:
        año = año_match.group(1)
    else:
        año = "Desconocido"
    
    # Extraer el nombre del jugador (todo lo que queda después del año y antes de .csv)
    jugador_match = re.search(r'\d{4}_(.*?)\.csv', nombre_archivo)
    if jugador_match:
        jugador = jugador_match.group(1).replace('_', ' ')
    else:
        jugador = "Desconocido"
    
    return año, jugador

def normalizar_fecha(fecha, año):
    """
    Normaliza la fecha a un formato estándar YYYY-MM-DD.
    Maneja diferentes formatos de entrada.
    """
    if pd.isna(fecha) or fecha == '':
        return ''
    
    fecha_str = str(fecha).strip()
    
    # Si ya está en formato YYYY-MM-DD, devolver tal cual
    if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_str):
        return fecha_str
    
    # Si la fecha ya incluye el año, intentar convertirla
    try:
        if "-" in fecha_str or "/" in fecha_str:
            # Intentar varios formatos comunes
            for formato in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%Y/%m/%d']:
                try:
                    fecha_obj = datetime.datetime.strptime(fecha_str, formato)
                    return fecha_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
        # Si no tiene formato reconocible, verificar si es solo mes y día
        partes = re.split(r'[-/]', fecha_str)
        if len(partes) == 2:
            # Asumir DD/MM o MM/DD
            try:
                if int(partes[0]) <= 12 and int(partes[1]) <= 31:  # Podría ser MM/DD
                    return f"{año}-{int(partes[0]):02d}-{int(partes[1]):02d}"
                else:  # Asumir DD/MM
                    return f"{año}-{int(partes[1]):02d}-{int(partes[0]):02d}"
            except ValueError:
                pass
    except Exception as e:
        print(f"Error al normalizar fecha '{fecha_str}': {e}")
    
    # Si todo falla, devolver la fecha original
    return fecha_str

def es_fila_valida(fila):
    """
    Determina si una fila contiene datos válidos o es una fila vacía/sin información útil.
    Descarta filas si las columnas "Equipo" y "Oponente" están vacías.
    Devuelve True si la fila es válida, False si debe ser descartada.
    """
    # Verificar si las columnas "Equipo" y "Oponente" están vacías
    equipo_vacio = True
    oponente_vacio = True
    
    # Comprobar Equipo
    if 'Equipo' in fila.index:
        valor_equipo = str(fila['Equipo']).strip()
        if valor_equipo and valor_equipo not in ['N', '.', ',,,,,,', 'nan']:
            equipo_vacio = False
    
    # Comprobar Oponente
    if 'Oponente' in fila.index:
        valor_oponente = str(fila['Oponente']).strip()
        if valor_oponente and valor_oponente not in ['N', '.', ',,,,,,', 'nan']:
            oponente_vacio = False
    
    # Si ambas están vacías, descartar la fila
    if equipo_vacio and oponente_vacio:
        return False
    
    # Contar cuántos valores no vacíos hay en la fila
    valores_no_vacios = sum(1 for valor in fila if pd.notna(valor) and str(valor).strip() != '')
    
    # Si casi todos los valores son vacíos, considerar la fila como inválida
    if valores_no_vacios <= 3:  # Solo tiene el ID y quizás 1-2 valores más
        return False
    
    # Por defecto, si hay suficiente información útil, mantener la fila
    return True

def filtrar_filas_vacias(df):
    """
    Filtra las filas del DataFrame que no contienen datos útiles.
    """
    if df.empty:
        return df
    
    # Aplicar la función es_fila_valida a cada fila
    filas_validas = df.apply(es_fila_valida, axis=1)
    df_filtrado = df[filas_validas]
    
    filas_eliminadas = len(df) - len(df_filtrado)
    if filas_eliminadas > 0:
        print(f"Se eliminaron {filas_eliminadas} filas sin datos útiles.")
    
    return df_filtrado

def unificar_columnas(df, año, jugador):
    """
    Unifica las columnas del DataFrame según el formato esperado.
    Añade o renombra columnas según sea necesario.
    """
    # Crear una copia para evitar warnings de modificación
    df = df.copy()
    
    # 1. Renombrar columnas si es necesario (conversion de formato inglés a español)
    columnas_actuales = df.columns.tolist()
    for col_antigua, col_nueva in MAPEO_COLUMNAS.items():
        if col_antigua in columnas_actuales and col_nueva not in columnas_actuales:
            df.rename(columns={col_antigua: col_nueva}, inplace=True)
    
    # 2. Normalizar la columna de fecha
    if 'Fecha' in df.columns:
        df['Fecha'] = df['Fecha'].apply(lambda x: normalizar_fecha(x, año))
    elif 'Date' in df.columns:
        df['Fecha'] = df['Date'].apply(lambda x: normalizar_fecha(x, año))
        df.drop('Date', axis=1, inplace=True, errors='ignore')
    else:
        # Si no hay columna de fecha, crearla con un valor predeterminado
        df['Fecha'] = f"{año}-01-01"  # 1 de enero del año como placeholder
    
    # 3. Asegurar que existe la columna Jugador
    if 'Jugador' not in df.columns:
        df['Jugador'] = jugador
    
    # 4. Asegurar que existe la columna Temporada
    if 'Temporada' not in df.columns:
        df['Temporada'] = año
    
    # 5. Crear columnas faltantes con valores vacíos
    for columna in COLUMNAS_ESPERADAS:
        if columna not in df.columns:
            df[columna] = ""
    
    # 6. Convertir columnas numéricas
    columnas_numericas = [
        "Minutos", "Goles", "Asistencias", "Penales marcados", 
        "Penales intentados", "Tiros totales", "Tiros a puerta", 
        "Tarjetas amarillas", "Tarjetas rojas", "Faltas cometidas", 
        "Faltas recibidas", "Fuera de juego", "Centros", 
        "Entradas ganadas", "Intercepciones", "Goles en propia", 
        "Penales ganados", "Penales concedidos"
    ]
    
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    return df

def procesar_archivo(ruta_archivo):
    """
    Procesa un solo archivo CSV y devuelve un DataFrame normalizado.
    """
    try:
        # Leer el archivo CSV
        df = pd.read_csv(ruta_archivo)
        
        # Extraer año y nombre del jugador del nombre del archivo
        nombre_archivo = os.path.basename(ruta_archivo)
        año, jugador = extraer_informacion_archivo(nombre_archivo)
        
        # Filtrar filas vacías o sin datos útiles
        df = filtrar_filas_vacias(df)
        
        # Normalizar las columnas según el formato esperado
        df_normalizado = unificar_columnas(df, año, jugador)
        
        print(f"Archivo {nombre_archivo} procesado correctamente. Filas: {len(df_normalizado)}")
        return df_normalizado
    
    except Exception as e:
        print(f"Error al procesar el archivo {ruta_archivo}: {e}")
        return None

def procesar_jugador(nombre_jugador):
    """
    Procesa todos los archivos de un jugador específico.
    Retorna un DataFrame con todos los datos del jugador unificados.
    """
    print(f"\n=== Procesando archivos para: {nombre_jugador} ===")
    
    # Preguntar cuántos archivos se unificarán para este jugador
    while True:
        try:
            num_archivos = int(input(f"Ingrese el número de archivos CSV para {nombre_jugador}: "))
            if num_archivos > 0:
                break
            else:
                print("Por favor, ingrese un número mayor que cero.")
        except ValueError:
            print("Por favor, ingrese un número válido.")
    
    # Lista para almacenar los dataframes de este jugador
    dataframes_jugador = []
    
    # Recopilar las rutas de los archivos
    for i in range(num_archivos):
        while True:
            ruta_archivo = input(f"Ingrese la ruta del archivo {i+1} para {nombre_jugador}: ")
            if os.path.exists(ruta_archivo) and ruta_archivo.lower().endswith('.csv'):
                # Procesar el archivo
                df_normalizado = procesar_archivo(ruta_archivo)
                
                if df_normalizado is not None:
                    dataframes_jugador.append(df_normalizado)
                    break
            else:
                print("El archivo no existe o no es un archivo CSV válido. Inténtelo de nuevo.")
    
    if dataframes_jugador:
        # Unificar todos los dataframes del jugador
        df_jugador_unificado = pd.concat(dataframes_jugador, ignore_index=True)
        
        # Asegurar que la columna 'Jugador' tenga el nombre correcto del jugador
        df_jugador_unificado['Jugador'] = nombre_jugador
        
        # Filtrar una vez más para asegurarnos de que no hay filas vacías
        df_jugador_unificado = filtrar_filas_vacias(df_jugador_unificado)
        
        # Ordenar por fecha
        if 'Fecha' in df_jugador_unificado.columns:
            df_jugador_unificado.sort_values(by='Fecha', inplace=True)
        
        print(f"Se han unificado {len(dataframes_jugador)} archivos para {nombre_jugador}.")
        return df_jugador_unificado
    else:
        print(f"No se ha podido unificar ningún archivo para {nombre_jugador}.")
        return None

def mostrar_resumen(df):
    """
    Muestra un resumen del DataFrame unificado.
    """
    print("\nResumen de los datos unificados:")
    print(f"Total de registros: {len(df)}")
    
    # Mostrar jugadores y partidos por jugador
    jugadores = df['Jugador'].unique()
    print(f"\nJugadores incluidos ({len(jugadores)}):")
    for jugador in jugadores:
        partidos = df[df['Jugador'] == jugador].shape[0]
        print(f"- {jugador}: {partidos} partidos")
    
    # Mostrar equipos
    equipos = df['Equipo'].unique()
    print(f"\nEquipos incluidos ({len(equipos)}):")
    for equipo in equipos:
        print(f"- {equipo}")
    
    # Mostrar competiciones
    if 'Competición' in df.columns:
        competiciones = df['Competición'].unique()
        print(f"\nCompeticiones incluidas ({len(competiciones)}):")
        for comp in competiciones:
            if pd.notna(comp) and comp != '':
                partidos = df[df['Competición'] == comp].shape[0]
                print(f"- {comp}: {partidos} partidos")
    
    # Mostrar estadísticas de goles
    if 'Goles' in df.columns:
        total_goles = df['Goles'].sum()
        print(f"\nTotal de goles: {total_goles}")
        for jugador in jugadores:
            goles = df[df['Jugador'] == jugador]['Goles'].sum()
            if goles > 0:
                print(f"- {jugador}: {goles} goles")

def main():
    print("=== UNIFICADOR DE ESTADÍSTICAS DE JUGADORES DE FÚTBOL ===")
    print("Este programa unifica archivos CSV de estadísticas de jugadores en un único archivo.")
    print("Los archivos deben tener el formato: YYYY_NombreJugador.csv")
    
    # Preguntar cuántos jugadores se procesarán
    while True:
        try:
            num_jugadores = int(input("\nIngrese el número de jugadores a procesar: "))
            if num_jugadores > 0:
                break
            else:
                print("Por favor, ingrese un número mayor que cero.")
        except ValueError:
            print("Por favor, ingrese un número válido.")
    
    # Lista para almacenar los dataframes de todos los jugadores
    dataframes_todos_jugadores = []
    
    # Procesar cada jugador
    for i in range(num_jugadores):
        nombre_jugador = input(f"\nIngrese el nombre del jugador {i+1}: ")
        df_jugador = procesar_jugador(nombre_jugador)
        
        if df_jugador is not None:
            dataframes_todos_jugadores.append(df_jugador)
    
    if dataframes_todos_jugadores:
        # Unificar todos los dataframes de todos los jugadores
        df_unificado_final = pd.concat(dataframes_todos_jugadores, ignore_index=True)
        
        # Filtrar filas vacías una última vez
        df_unificado_final = filtrar_filas_vacias(df_unificado_final)
        
        # Crear directorio data si no existe
        directorio_data = "data"
        if not os.path.exists(directorio_data):
            os.makedirs(directorio_data)
            print(f"Se ha creado el directorio '{directorio_data}' para guardar el archivo.")
        
        # Reordenar columnas para que las más importantes estén primero
        columnas_ordenadas = ['Jugador', 'Temporada', 'Fecha', 'Competición', 'Equipo', 'Oponente', 
                             'Resultado', 'Goles', 'Asistencias']
        
        # Añadir el resto de columnas
        for columna in df_unificado_final.columns:
            if columna not in columnas_ordenadas:
                columnas_ordenadas.append(columna)
        
        # Reordenar el DataFrame
        df_unificado_final = df_unificado_final[
            [col for col in columnas_ordenadas if col in df_unificado_final.columns]
        ]
        
        # Guardar el dataframe unificado en la carpeta data
        nombre_salida = input("\nIngrese el nombre para el archivo unificado (ej: datos_unificados.csv): ")
        if not nombre_salida.lower().endswith('.csv'):
            nombre_salida += '.csv'
        
        ruta_completa = os.path.join(directorio_data, nombre_salida)
        df_unificado_final.to_csv(ruta_completa, index=False)
        print(f"\nArchivo unificado guardado como: {ruta_completa}")
        
        # Mostrar un resumen de los datos
        mostrar_resumen(df_unificado_final)
        
        print("\n¡Proceso completado con éxito!")
    else:
        print("No se ha podido unificar ningún archivo.")

if __name__ == "__main__":
    main()