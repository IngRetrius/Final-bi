import pandas as pd
import os
import re
import datetime

# Lista de columnas esperadas en el nuevo formato para porteros
COLUMNAS_ESPERADAS = [
    "partido", "Fecha", "Día de la semana", "Competición", "Ronda o Fase", 
    "Sede", "Resultado", "Equipo", "Oponente", "Titular", "Posición", 
    "Minutos", "Tiros a puerta recibidos", "Goles encajados", "Paradas", 
    "Porcentaje de paradas", "Porterías a cero", "Penales recibidos", 
    "Penales permitidos", "Penales atajados", "Penales fallados"
]

# Mapeo opcional de nombres de columnas antiguos a nuevos para porteros
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
    "SoTA": "Tiros a puerta recibidos",
    "GA": "Goles encajados",
    "Saves": "Paradas",
    "Save%": "Porcentaje de paradas",
    "CS": "Porterías a cero",
    "PKatt": "Penales recibidos",
    "PKA": "Penales permitidos",
    "PKsv": "Penales atajados",
    "PKm": "Penales fallados"
}

def extraer_informacion_archivo(nombre_archivo):
    """
    Extrae el año y el nombre del portero del nombre del archivo.
    El formato esperado es: YYYY_NombrePortero_portero.csv
    """
    # Extraer el año usando una expresión regular
    año_match = re.search(r'(\d{4})_', nombre_archivo)
    if año_match:
        año = año_match.group(1)
    else:
        año = "Desconocido"
    
    # Extraer el nombre del portero (todo lo que queda después del año y antes de _portero.csv)
    portero_match = re.search(r'\d{4}_(.*?)\.csv', nombre_archivo)
    if portero_match:
        portero = portero_match.group(1).replace('_', ' ')
    else:
        portero = "Desconocido"
    
    return año, portero

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

def unificar_columnas(df, año, portero):
    """
    Unifica las columnas del DataFrame según el formato esperado para porteros.
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
    
    # 3. Asegurar que existe la columna Portero
    if 'Portero' not in df.columns:
        df['Portero'] = portero
    
    # 4. Asegurar que existe la columna Temporada
    if 'Temporada' not in df.columns:
        df['Temporada'] = año
    
    # 5. Crear columnas faltantes con valores vacíos
    for columna in COLUMNAS_ESPERADAS:
        if columna not in df.columns:
            df[columna] = ""
    
    # 6. Convertir columnas numéricas específicas para porteros
    columnas_numericas = [
        "Minutos", "Tiros a puerta recibidos", "Goles encajados", "Paradas", 
        "Porterías a cero", "Penales recibidos", "Penales permitidos", 
        "Penales atajados", "Penales fallados"
    ]
    
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    # 7. Tratamiento especial para el porcentaje de paradas
    if 'Porcentaje de paradas' in df.columns:
        # Convertir a float, eliminar símbolos %, etc.
        df['Porcentaje de paradas'] = df['Porcentaje de paradas'].astype(str).str.replace('%', '')
        df['Porcentaje de paradas'] = pd.to_numeric(df['Porcentaje de paradas'], errors='coerce').fillna(0)
        # Asegurar formato de porcentaje (valores entre 0 y 1)
        df['Porcentaje de paradas'] = df['Porcentaje de paradas'].apply(
            lambda x: x/100 if x > 1 else x
        )
    
    # 8. Asegurar que la posición es "GK" para todos los porteros
    if 'Posición' in df.columns:
        df['Posición'] = 'GK'
    
    return df

def procesar_archivo(ruta_archivo):
    """
    Procesa un solo archivo CSV de portero y devuelve un DataFrame normalizado.
    """
    try:
        # Leer el archivo CSV
        df = pd.read_csv(ruta_archivo)
        
        # Extraer año y nombre del portero del nombre del archivo
        nombre_archivo = os.path.basename(ruta_archivo)
        año, portero = extraer_informacion_archivo(nombre_archivo)
        
        # Filtrar filas vacías o sin datos útiles
        df = filtrar_filas_vacias(df)
        
        # Normalizar las columnas según el formato esperado para porteros
        df_normalizado = unificar_columnas(df, año, portero)
        
        print(f"Archivo {nombre_archivo} procesado correctamente. Filas: {len(df_normalizado)}")
        return df_normalizado
    
    except Exception as e:
        print(f"Error al procesar el archivo {ruta_archivo}: {e}")
        return None

def procesar_portero(nombre_portero):
    """
    Procesa todos los archivos de un portero específico.
    Retorna un DataFrame con todos los datos del portero unificados.
    """
    print(f"\n=== Procesando archivos para el portero: {nombre_portero} ===")
    
    # Preguntar cuántos archivos se unificarán para este portero
    while True:
        try:
            num_archivos = int(input(f"Ingrese el número de archivos CSV para {nombre_portero}: "))
            if num_archivos > 0:
                break
            else:
                print("Por favor, ingrese un número mayor que cero.")
        except ValueError:
            print("Por favor, ingrese un número válido.")
    
    # Lista para almacenar los dataframes de este portero
    dataframes_portero = []
    
    # Recopilar las rutas de los archivos
    for i in range(num_archivos):
        while True:
            ruta_archivo = input(f"Ingrese la ruta del archivo {i+1} para {nombre_portero}: ")
            if os.path.exists(ruta_archivo) and ruta_archivo.lower().endswith('.csv'):
                # Procesar el archivo
                df_normalizado = procesar_archivo(ruta_archivo)
                
                if df_normalizado is not None:
                    dataframes_portero.append(df_normalizado)
                    break
            else:
                print("El archivo no existe o no es un archivo CSV válido. Inténtelo de nuevo.")
    
    if dataframes_portero:
        # Unificar todos los dataframes del portero
        df_portero_unificado = pd.concat(dataframes_portero, ignore_index=True)
        
        # Asegurar que la columna 'Portero' tenga el nombre correcto del portero
        df_portero_unificado['Portero'] = nombre_portero
        
        # Filtrar una vez más para asegurarnos de que no hay filas vacías
        df_portero_unificado = filtrar_filas_vacias(df_portero_unificado)
        
        # Ordenar por fecha
        if 'Fecha' in df_portero_unificado.columns:
            df_portero_unificado.sort_values(by='Fecha', inplace=True)
        
        print(f"Se han unificado {len(dataframes_portero)} archivos para {nombre_portero}.")
        return df_portero_unificado
    else:
        print(f"No se ha podido unificar ningún archivo para {nombre_portero}.")
        return None

def mostrar_resumen(df):
    """
    Muestra un resumen del DataFrame unificado para porteros.
    """
    print("\nResumen de los datos unificados:")
    print(f"Total de registros: {len(df)}")
    
    # Mostrar porteros y partidos por portero
    porteros = df['Portero'].unique()
    print(f"\nPorteros incluidos ({len(porteros)}):")
    for portero in porteros:
        partidos = df[df['Portero'] == portero].shape[0]
        print(f"- {portero}: {partidos} partidos")
    
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
    
    # Estadísticas de portero
    if 'Goles encajados' in df.columns:
        total_goles_encajados = df['Goles encajados'].sum()
        print(f"\nTotal de goles encajados: {total_goles_encajados}")
        for portero in porteros:
            goles_encajados = df[df['Portero'] == portero]['Goles encajados'].sum()
            print(f"- {portero}: {goles_encajados} goles encajados")
    
    # Estadísticas de porterías a cero
    if 'Porterías a cero' in df.columns:
        total_porterias_cero = df['Porterías a cero'].sum()
        print(f"\nTotal de porterías a cero: {total_porterias_cero}")
        for portero in porteros:
            porterias_cero = df[df['Portero'] == portero]['Porterías a cero'].sum()
            print(f"- {portero}: {porterias_cero} porterías a cero")
    
    # Estadísticas de penales atajados
    if 'Penales atajados' in df.columns:
        total_penales_atajados = df['Penales atajados'].sum()
        if total_penales_atajados > 0:
            print(f"\nTotal de penales atajados: {total_penales_atajados}")
            for portero in porteros:
                penales_atajados = df[df['Portero'] == portero]['Penales atajados'].sum()
                if penales_atajados > 0:
                    penales_enfrentados = df[df['Portero'] == portero]['Penales recibidos'].sum()
                    if penales_enfrentados > 0:
                        porcentaje = (penales_atajados / penales_enfrentados) * 100
                        print(f"- {portero}: {penales_atajados} penales atajados ({porcentaje:.1f}%)")

def main():
    print("=== UNIFICADOR DE ESTADÍSTICAS DE PORTEROS DE FÚTBOL ===")
    print("Este programa unifica archivos CSV de estadísticas de porteros en un único archivo.")
    print("Los archivos deben tener el formato: YYYY_NombrePortero_portero.csv")
    
    # Preguntar cuántos porteros se procesarán
    while True:
        try:
            num_porteros = int(input("\nIngrese el número de porteros a procesar: "))
            if num_porteros > 0:
                break
            else:
                print("Por favor, ingrese un número mayor que cero.")
        except ValueError:
            print("Por favor, ingrese un número válido.")
    
    # Lista para almacenar los dataframes de todos los porteros
    dataframes_todos_porteros = []
    
    # Procesar cada portero
    for i in range(num_porteros):
        nombre_portero = input(f"\nIngrese el nombre del portero {i+1}: ")
        df_portero = procesar_portero(nombre_portero)
        
        if df_portero is not None:
            dataframes_todos_porteros.append(df_portero)
    
    if dataframes_todos_porteros:
        # Unificar todos los dataframes de todos los porteros
        df_unificado_final = pd.concat(dataframes_todos_porteros, ignore_index=True)
        
        # Filtrar filas vacías una última vez
        df_unificado_final = filtrar_filas_vacias(df_unificado_final)
        
        # Crear directorio data si no existe
        directorio_data = "data"
        if not os.path.exists(directorio_data):
            os.makedirs(directorio_data)
            print(f"Se ha creado el directorio '{directorio_data}' para guardar el archivo.")
        
        # Reordenar columnas para que las más importantes estén primero
        columnas_ordenadas = ['Portero', 'Temporada', 'Fecha', 'Competición', 'Equipo', 'Oponente', 
                             'Resultado', 'Tiros a puerta recibidos', 'Goles encajados', 'Paradas',
                             'Porcentaje de paradas', 'Porterías a cero']
        
        # Añadir columnas de penales
        columnas_penales = ['Penales recibidos', 'Penales permitidos', 'Penales atajados', 'Penales fallados']
        for col in columnas_penales:
            if col not in columnas_ordenadas:
                columnas_ordenadas.append(col)
        
        # Añadir el resto de columnas
        for columna in df_unificado_final.columns:
            if columna not in columnas_ordenadas:
                columnas_ordenadas.append(columna)
        
        # Reordenar el DataFrame
        df_unificado_final = df_unificado_final[
            [col for col in columnas_ordenadas if col in df_unificado_final.columns]
        ]
        
        # Guardar el dataframe unificado en la carpeta data
        nombre_salida = input("\nIngrese el nombre para el archivo unificado (ej: porteros_unificados.csv): ")
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