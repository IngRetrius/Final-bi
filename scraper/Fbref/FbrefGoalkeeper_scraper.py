"""
Scraper especializado para extraer datos de partidos de porteros de FBref
Versión final con formato simplificado
"""

import time
import os
import argparse
import re
import traceback
import datetime
import csv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

# Configuración base
DATA_FOLDER = "data/"
PLAYERS_FOLDER = "Porteros seleccionados"

# Headers para simular un navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Campos a extraer de FBref y sus correspondientes data-stat
# Campos a extraer de FBref y sus correspondientes data-stat
CAMPO_A_DATA_STAT = {
    "Date": "date",
    "Day": "dayofweek",
    "Comp": "comp",
    "Round": "round", 
    "Venue": "venue",
    "Result": "result",
    "Squad": "team",
    "Opponent": "opponent",
    "Start": "game_started",
    "Pos": "position",
    "Min": "minutes",
    "SoTA": "gk_shots_on_target_against",  # Cambiado
    "GA": "gk_goals_against",              # Cambiado
    "Saves": "gk_saves",                   # Cambiado
    "Save%": "gk_save_pct",                # Cambiado
    "CS": "gk_clean_sheets",               # Cambiado
    "PKatt": "gk_pens_att",                # Cambiado
    "PKA": "gk_pens_allowed",              # Cambiado
    "PKsv": "gk_pens_saved",               # Cambiado
    "PKm": "gk_pens_missed"                # Cambiado
}

# Lista ordenada de campos
CAMPOS = list(CAMPO_A_DATA_STAT.keys())

# Mapeo de acrónimos a nombres completos en español
ACRONIMO_A_NOMBRE_COMPLETO = {
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

def create_driver(browser_type='firefox', visible=True):
    """Crea y configura el driver del navegador elegido"""
    print(f"Configurando el navegador {browser_type}...")
    
    if browser_type.lower() == 'firefox':
        options = FirefoxOptions()
        if not visible:
            options.add_argument("--headless")
        options.set_preference("general.useragent.override", HEADERS["User-Agent"])
        options.set_preference("dom.webnotifications.enabled", False)
        options.set_preference("dom.push.enabled", False)
        
        try:
            driver = webdriver.Firefox(options=options)
            print("Firefox inicializado correctamente")
            return driver
        except Exception as e:
            print(f"Error al inicializar Firefox: {e}")
            raise
    
    elif browser_type.lower() == 'chrome':
        options = ChromeOptions()
        if not visible:
            options.add_argument("--headless=new")
        options.add_argument(f"user-agent={HEADERS['User-Agent']}")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        
        try:
            driver = webdriver.Chrome(options=options)
            print("Chrome inicializado correctamente")
            return driver
        except Exception as e:
            print(f"Error al inicializar Chrome: {e}")
            raise
    
    else:
        print(f"Navegador {browser_type} no soportado. Usando Firefox por defecto.")
        return create_driver('firefox', visible)

def navigate_to_page(driver, url):
    """Navega a la página del jugador en FBref"""
    try:
        driver.get(url)
        print(f"Navegando a: {url}")
        time.sleep(5)  # Esperar a que la página cargue completamente
        
        # Verificar si hay un banner de cookies y cerrarlo
        try:
            cookie_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Accept') or contains(text(), 'I Accept') or contains(text(), 'Agree') or contains(text(), 'OK')]")
            
            if cookie_buttons:
                cookie_buttons[0].click()
                print("Banner de cookies cerrado")
                time.sleep(1)
        except:
            print("No se encontró banner de cookies o ya fue aceptado")
        
        print(f"Título de la página: {driver.title}")
        return True
    except Exception as e:
        print(f"Error al navegar a la página: {e}")
        print(traceback.format_exc())
        return False

def extract_player_info(driver, url):
    """Extrae la información básica del jugador desde la URL y la página"""
    player_info = {
        "nombre": "Desconocido",
        "equipo": "Desconocido",
        "año": str(datetime.datetime.now().year),
        "id": "Desconocido"
    }
    
    try:
        # Extraer año y nombre del jugador directamente de la URL
        url_pattern_with_year = r"players/([^/]+)/matchlogs/(\d{4})/([^/]+)"
        url_match_with_year = re.search(url_pattern_with_year, url)
        
        if url_match_with_year:
            player_id = url_match_with_year.group(1)
            year = url_match_with_year.group(2)
            player_name_encoded = url_match_with_year.group(3)
            
            player_info["id"] = player_id
            player_info["año"] = year
            
            # Limpiar el nombre del jugador
            player_name = player_name_encoded.replace('-', ' ')
            player_name = re.sub(r'Match[ -]Logs', '', player_name).strip()
            player_name = re.sub(r'Goalkeeping', '', player_name).strip()
            player_info["nombre"] = player_name
        
        # Si no pudimos extraer de la URL, intentar desde el título
        if player_info["nombre"] == "Desconocido":
            title = driver.title
            title_parts = title.split('|')[0].strip()
            if title_parts:
                player_info["nombre"] = title_parts
        
        # Extraer nombre del equipo - buscar imagen del jugador
        try:
            img_elements = driver.find_elements(By.XPATH, "//img[contains(@class, 'headshot') or contains(@class, 'player')]")
            if img_elements:
                for img in img_elements:
                    alt_text = img.get_attribute("alt")
                    if alt_text and "headshot" in alt_text:
                        player_info["equipo"] = alt_text
                        break
            
            # Intentar extraer de otros elementos si aún no tenemos el equipo
            if player_info["equipo"] == "Desconocido":
                team_elements = driver.find_elements(By.XPATH, 
                    "//strong[contains(text(), 'Current Team:')]/following-sibling::a[1] | //div[@class='filter']/div[contains(text(), 'Team')]")
                if team_elements:
                    player_info["equipo"] = team_elements[0].text.strip()
        except:
            print("No se pudo encontrar el nombre del equipo")
        
        # Verificar si es un portero
        try:
            # Buscar encabezados específicos de portero
            gk_indicators = driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'Goalkeeping') or contains(text(), 'SoTA') or contains(text(), 'Save%') or contains(text(), 'Clean Sheets')]")
            
            if not gk_indicators:
                print("⚠️ ADVERTENCIA: Esta página podría no corresponder a un portero.")
                print("Se recomienda verificar que la URL sea de un portero.")
            else:
                print("✅ Confirmado: La página corresponde a un portero.")
        except:
            print("No se pudo determinar si el jugador es un portero.")
        
        print(f"Información del jugador extraída: {player_info}")
        return player_info
    except Exception as e:
        print(f"Error al extraer información del jugador: {e}")
        print(traceback.format_exc())
        return player_info

def extract_matches_from_fbref(driver):
    """Extrae datos de partidos directamente de la estructura específica de FBref, omitiendo encabezados"""
    print("Extrayendo datos de partidos de FBref...")
    
    matches_data = []
    match_id = 1
    
    try:
        # Primero buscamos las filas de datos que no sean encabezados o filas especiales
        rows = driver.find_elements(By.XPATH, "//tr[not(contains(@class, 'thead')) and not(contains(@class, 'over_header')) and not(contains(@class, 'spacer'))]")
        print(f"Se encontraron {len(rows)} filas potenciales de datos")
        
        for row in rows:
            # Verificar si esta fila tiene una celda de fecha válida (th o td con data-stat="date")
            date_cells = row.find_elements(By.XPATH, ".//th[@data-stat='date'] | .//td[@data-stat='date']")
            
            if not date_cells:
                continue  # Si no tiene celda de fecha, pasar a la siguiente fila
            
            date_cell = date_cells[0]
            
            # NUEVO: Detección de encabezados - verificar si la celda contiene un texto que indica que es un encabezado
            date_text = date_cell.text.strip()
            
            # Si la celda de fecha contiene textos como "Date", "Fecha", o está vacía, probablemente es un encabezado
            if date_text.lower() in ["date", "fecha", "dat", ""]:
                print(f"Omitiendo fila de encabezado: {date_text}")
                continue
            
            # NUEVO: También verificamos si la fila contiene principalmente elementos th (encabezados)
            th_elements = row.find_elements(By.TAG_NAME, "th")
            if len(th_elements) > 2:  # Si hay más de 2 elementos th, probablemente es un encabezado
                print("Omitiendo fila con múltiples elementos th (probable encabezado)")
                continue
            
            # Intentar obtener la fecha del atributo csk primero (más preciso)
            csk_date = date_cell.get_attribute("csk")
            
            # Si no hay csk, intentar obtener del texto o enlaces dentro de la celda
            if not csk_date:
                date_links = date_cell.find_elements(By.TAG_NAME, "a")
                
                if date_links:
                    href = date_links[0].get_attribute("href")
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', href)
                    if date_match:
                        date_text = date_match.group(1)
                
                if not date_text:
                    continue  # Sin fecha, no podemos procesar esta fila
                    
                formatted_date = date_text
            else:
                # Formatear la fecha del csk (formato YYYYMMDD)
                try:
                    if len(csk_date) == 8:  # Formato YYYYMMDD
                        formatted_date = f"{csk_date[:4]}-{csk_date[4:6]}-{csk_date[6:8]}"
                    else:
                        formatted_date = csk_date
                except:
                    formatted_date = csk_date
            
            # NUEVO: Validación adicional - verificar si parece una fecha válida
            # Si no tiene al menos un número o guión, probablemente no es una fecha
            if not any(c.isdigit() or c == '-' for c in formatted_date):
                print(f"Omitiendo fila con fecha no válida: {formatted_date}")
                continue
            
            # Crear datos para este partido
            match_data = {
                "partido": str(match_id),
                "Date": formatted_date
            }
            
            # Extraer el resto de campos directamente usando los selectores data-stat
            for campo, data_stat in CAMPO_A_DATA_STAT.items():
                if campo == "Date":  # Ya lo tenemos de arriba
                    continue
                
                try:
                    # Buscar la celda específica con el data-stat exacto
                    cells = row.find_elements(By.XPATH, f"./td[@data-stat='{data_stat}']")
                    
                    if cells:
                        cell = cells[0]
                        # Obtener el texto directamente
                        match_data[campo] = cell.text.strip()
                    else:
                        # Si no encontramos la celda, intentar con una búsqueda más amplia
                        broader_cells = row.find_elements(By.XPATH, f".//*[@data-stat='{data_stat}']")
                        if broader_cells:
                            match_data[campo] = broader_cells[0].text.strip()
                        else:
                            match_data[campo] = ""
                except Exception as cell_error:
                    print(f"Error al extraer {campo}: {cell_error}")
                    match_data[campo] = ""
            
            # Añadir este partido a la lista solo si tiene contenido suficiente
            if any(value for key, value in match_data.items() if key != "partido"):
                matches_data.append(match_data)
                print(f"Extraído partido {match_id}: {formatted_date}")
                match_id += 1
    
    except Exception as e:
        print(f"Error en extracción principal: {e}")
        print(traceback.format_exc())
    
    # Si no se encontraron datos, intentar con un enfoque JavaScript
    if not matches_data:
        # ... código JavaScript existente ...
    
        print(f"Total de partidos extraídos: {len(matches_data)}")
    return matches_data

def process_matches_data(matches_data, player_info):
    """Procesa y limpia los datos de partidos extraídos"""
    if not matches_data:
        return []
    
    print(f"Procesando {len(matches_data)} partidos...")
    
    # Función para convertir fechas a valor ordenable
    def fecha_a_valor_ordenable(partido):
        try:
            if 'Date' in partido and partido['Date']:
                fecha_str = partido['Date']
                
                # YYYY-MM-DD (formato estándar de FBref en URLs)
                if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_str):
                    partes = fecha_str.split('-')
                    return int(partes[0]) * 10000 + int(partes[1]) * 100 + int(partes[2])
                
                # DD-MM-YYYY o DD/MM/YYYY
                if re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}$', fecha_str):
                    partes = re.split(r'[-/]', fecha_str)
                    return int(partes[2]) * 10000 + int(partes[1]) * 100 + int(partes[0])
                
                # Mes textual (Apr 14, 2024)
                match = re.search(r'(\w+)\s+(\d+),?\s*(\d{4})?', fecha_str)
                if match:
                    meses = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 
                            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                    mes_str = match.group(1)
                    mes = meses.get(mes_str[:3], 1)
                    dia = int(match.group(2))
                    año = int(match.group(3) if match.group(3) else player_info["año"])
                    return año * 10000 + mes * 100 + dia
            
            return 0
        except Exception as e:
            print(f"Error procesando fecha '{partido.get('Date', '')}': {e}")
            return 0
    
    # Normalizar fechas en formato consistente
    for partido in matches_data:
        if 'Date' in partido and partido['Date']:
            fecha_str = partido['Date']
            
            # Intentar extraer año-mes-día desde varios formatos
            
            # Si ya está en YYYY-MM-DD, dejarlo así
            if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_str):
                continue
                
            # Intentar extraer de formatos con año primero (YYYY/MM/DD)
            match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', fecha_str)
            if match:
                partido['Date'] = f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
                continue
                
            # Intentar extraer de formatos con día primero (DD/MM/YYYY)
            match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', fecha_str)
            if match:
                partido['Date'] = f"{match.group(3)}-{int(match.group(2)):02d}-{int(match.group(1)):02d}"
                continue
                
            # Intentar extraer de formatos textuales (Jan 25, 2023)
            match = re.search(r'(\w+)\s+(\d+),?\s*(\d{4})?', fecha_str)
            if match:
                meses = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 
                        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                mes_str = match.group(1)
                mes = meses.get(mes_str[:3], 1)
                dia = int(match.group(2))
                año = int(match.group(3) if match.group(3) else player_info["año"])
                partido['Date'] = f"{año}-{mes:02d}-{dia:02d}"
    
    # Ordenar partidos por fecha
    matches_data.sort(key=fecha_a_valor_ordenable)
    
    # Reasignar IDs secuenciales
    for idx, partido in enumerate(matches_data, 1):
        partido['partido'] = str(idx)
    
    # Resto de la limpieza de datos (específico para porteros)
    for partido in matches_data:
        # Normalizar Result
        if 'Result' in partido and partido['Result']:
            result_match = re.match(r'^([WLDTwldt])\s*(.*)$', partido['Result'])
            if result_match:
                letter = result_match.group(1).upper()
                score = result_match.group(2).strip()
                partido['Result'] = f"{letter} {score}"
        
        # Normalizar Start
        if 'Start' in partido:
            if partido['Start'] and 'Y' in partido['Start'].upper():
                partido['Start'] = 'Y*' if '*' in partido['Start'] else 'Y'
            else:
                partido['Start'] = 'N'
        
        # Normalizar Pos - Asegurar que sea GK para porteros
        if 'Pos' in partido:
            if partido['Pos'] != 'GK':
                print(f"⚠️ ADVERTENCIA: Posición no coincide con GK en partido {partido['partido']}: {partido['Pos']}. Cambiando a GK.")
                partido['Pos'] = 'GK'
        else:
            partido['Pos'] = 'GK'  # Establecer por defecto
        
        # Convertir valores vacíos a "0" en campos numéricos específicos de porteros
        numeric_fields = ["SoTA", "GA", "Saves", "CS", "PKatt", "PKA", "PKsv", "PKm"]
        
        for field in numeric_fields:
            if field in partido:
                try:
                    if not partido[field] or not re.match(r'^[\d\.]+$', partido[field].strip()):
                        partido[field] = "0"
                except:
                    partido[field] = "0"
        
        # Manejar el campo Save% de manera especial
        if 'Save%' in partido:
            if not partido['Save%'] or partido['Save%'] == '':
                partido['Save%'] = "0.0"
            elif partido['Save%'].endswith('%'):
                # Convertir de porcentaje a decimal
                try:
                    save_pct = partido['Save%'].rstrip('%')
                    save_decimal = float(save_pct) / 100
                    partido['Save%'] = f"{save_decimal:.3f}"
                except:
                    partido['Save%'] = "0.0"
    
    return matches_data

def save_matches_to_csv(matches_data, file_path):
    """Guarda los datos de partidos en un archivo CSV"""
    try:
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            # Crear encabezados CSV
            fieldnames = ['partido'] + CAMPOS
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Escribir encabezados traducidos
            header_row = {field: ACRONIMO_A_NOMBRE_COMPLETO.get(field, field) for field in fieldnames}
            header_row['partido'] = 'partido'
            writer.writerow(header_row)
            
            # Escribir datos
            for partido in matches_data:
                writer.writerow(partido)
        
        print(f"Datos guardados en {file_path}")
        return True
    except Exception as e:
        print(f"Error al guardar el archivo CSV: {e}")
        print(traceback.format_exc())
        return False

def scrape_fbref(url, browser_type='firefox', visible=True, timeout=60, wait=5):
    """Función principal de scraping que integra todo el proceso"""
    driver = None
    
    try:
        # Inicializar driver
        driver = create_driver(browser_type, visible)
        driver.set_page_load_timeout(timeout)
        
        # Navegar a la página
        if not navigate_to_page(driver, url):
            return False
        
        # Esperar carga completa
        time.sleep(wait)
        
        # Extraer información del jugador
        player_info = extract_player_info(driver, url)
        
        # Crear estructura de carpetas
        player_name = player_info["nombre"].replace(" ", "_")
        player_name = re.sub(r'[\\/:"*?<>|]', '', player_name)
        
        year = player_info["año"]
        
        base_folder = os.path.join(DATA_FOLDER, PLAYERS_FOLDER)
        player_folder = os.path.join(base_folder, player_name)
        
        for folder in [DATA_FOLDER, base_folder, player_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)
                print(f"Creada carpeta: {folder}")
        
        # Nombre de archivo simplificado: año y nombre del jugador
        file_name = f"{year}_{player_name}.csv"
        file_path = os.path.join(player_folder, file_name)
        
        # Extraer datos de partidos usando el método especializado para FBref
        matches_data = extract_matches_from_fbref(driver)
        
        # Procesar datos
        if matches_data:
            processed_matches = process_matches_data(matches_data, player_info)
            
            # Guardar en CSV
            if processed_matches and save_matches_to_csv(processed_matches, file_path):
                print(f"¡Éxito! Se extrajeron y guardaron {len(processed_matches)} partidos.")
                return True
        
        print("No se encontraron datos de partidos.")
        return False
    
    except Exception as e:
        print(f"Error durante el scraping: {e}")
        print(traceback.format_exc())
        return False
    
    finally:
        if driver:
            driver.quit()
            print("Navegador cerrado")

def main():
    """Función principal"""
    """Función principal"""
    parser = argparse.ArgumentParser(description='Scraper especializado para extraer datos de porteros de FBref')
    parser.add_argument('--visible', action='store_true', 
                        help='Ejecutar con navegador visible (no headless)')
    parser.add_argument('--url', type=str, default="",
                        help='URL de la página del jugador')
    parser.add_argument('--browser', type=str, default="firefox",
                        help='Navegador a utilizar (firefox, chrome)')
    parser.add_argument('--timeout', type=int, default=60,
                        help='Tiempo máximo de espera en segundos')
    parser.add_argument('--wait', type=int, default=5,
                        help='Tiempo de espera tras cargar la página')
    parser.add_argument('--retries', type=int, default=3,
                        help='Número de reintentos en caso de error')
    
    args = parser.parse_args()
    
    # Solicitar URL si no se proporcionó
    url = args.url
    if not url:
        print("\n=== Scraper especializado para porteros de FBref ===")
        url = input("Introduce la URL de la página del portero (presiona Enter para usar URL predeterminada): ")
        
        if not url:
            url = "https://fbref.com/en/players/70860ae2/matchlogs/2024/Goalkeeping/Camilo-Vargas-Match-Logs"
            print(f"Usando URL predeterminada: {url}")
    
    # Información del proceso
    print("\n=== Información del scraper para porteros ===")
    print(f"URL a procesar: {url}")
    print(f"Navegador: {args.browser}")
    print(f"Modo visible: {'Sí' if args.visible else 'No'}")
    print(f"Tiempo de espera: {args.timeout} segundos")
    print(f"Reintentos: {args.retries}")
    print("===============================\n")
    
    # Reintentos
    for retry in range(args.retries):
        if retry > 0:
            print(f"\nReintento {retry+1}/{args.retries}...")
        
        if scrape_fbref(url, args.browser, args.visible, args.timeout, args.wait):
            print("\n¡Proceso completado con éxito!")
            return
    
    print(f"\nSe alcanzó el máximo de reintentos ({args.retries}) sin éxito.")
    print("Sugerencias:")
    print("- Verifica que la URL sea correcta y corresponda a un portero")
    print("- Aumenta el tiempo de espera (--timeout)")
    print("- Prueba con navegador visible (--visible)")
    print("- Intenta con otro navegador (--browser chrome)")

if __name__ == "__main__":
    main()