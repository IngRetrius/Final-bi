"""
Scraper especializado para extraer datos de partidos de FBref
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
PLAYERS_FOLDER = "Jugadores seleccionados"

# Headers para simular un navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

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
    "Gls": "goals",
    "Ast": "assists",
    "PK": "pens_made",
    "PKatt": "pens_att",
    "Sh": "shots",
    "SoT": "shots_on_target",
    "CrdY": "cards_yellow",
    "CrdR": "cards_red",
    "Fls": "fouls",
    "Fld": "fouled",
    "Off": "offsides",
    "Crs": "crosses",
    "TklW": "tackles_won",
    "Int": "interceptions",
    "OG": "own_goals",
    "PKwon": "pens_won",
    "PKcon": "pens_conceded"
    # Se ha eliminado "Match Report": "match_report"
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
    # Se ha eliminado "Match Report": "Informe del partido"
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
        
        print(f"Información del jugador extraída: {player_info}")
        return player_info
    except Exception as e:
        print(f"Error al extraer información del jugador: {e}")
        print(traceback.format_exc())
        return player_info

def extract_matches_from_fbref(driver):
    """Extrae datos de partidos directamente de la estructura específica de FBref usando el atributo csk"""
    print("Extrayendo datos de partidos de FBref...")
    
    matches_data = []
    match_id = 1
    
    try:
        # 1. Intentar encontrar la tabla principal de partidos
        print("Buscando elementos con atributo csk para fechas...")
        
        # Este enfoque busca directamente las celdas de fecha con el atributo csk
        date_cells = driver.find_elements(By.XPATH, "//th[@data-stat='date' and @csk] | //td[@data-stat='date' and @csk]")
        
        if date_cells:
            print(f"Se encontraron {len(date_cells)} celdas de fecha con atributo csk")
            
            # Para cada celda de fecha, extraer datos de su fila
            for date_cell in date_cells:
                # Obtener la fecha del atributo csk
                csk_date = date_cell.get_attribute("csk")
                
                if not csk_date:
                    continue
                
                # Formatear la fecha (el csk suele tener formato YYYYMMDD)
                try:
                    if len(csk_date) == 8:  # Formato YYYYMMDD
                        formatted_date = f"{csk_date[:4]}-{csk_date[4:6]}-{csk_date[6:8]}"
                    else:
                        formatted_date = csk_date
                except:
                    formatted_date = csk_date
                
                # Obtener la fila completa
                row = date_cell.find_element(By.XPATH, "./parent::tr")
                
                # Verificar si es una fila deseada
                row_class = row.get_attribute("class") or ""
                if any(c in row_class for c in ["thead", "divider", "spacer", "over_header"]):
                    continue
                
                # Crear datos para este partido
                match_data = {
                    "partido": str(match_id),
                    "Date": formatted_date
                }
                
                # Extraer el resto de campos
                for campo, data_stat in CAMPO_A_DATA_STAT.items():
                    if campo == "Date":  # Ya lo tenemos del csk
                        continue
                    
                    try:
                        cell = row.find_element(By.XPATH, f".//td[@data-stat='{data_stat}']")
                        match_data[campo] = cell.text.strip()
                    except:
                        match_data[campo] = ""
                
                matches_data.append(match_data)
                match_id += 1
        else:
            print("No se encontraron celdas con atributo csk. Intentando otro método...")
            
            # Método alternativo: buscar cualquier th o td con data-stat="date"
            date_elements = driver.find_elements(By.XPATH, "//th[@data-stat='date'] | //td[@data-stat='date']")
            print(f"Se encontraron {len(date_elements)} elementos de fecha")
            
            for date_element in date_elements:
                # Intentar obtener la fecha del texto o enlaces
                date_text = date_element.text.strip()
                date_links = date_element.find_elements(By.TAG_NAME, "a")
                
                # Si hay un enlace, intentar extraer la fecha del href
                if date_links:
                    href = date_links[0].get_attribute("href")
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', href)
                    if date_match:
                        date_text = date_match.group(1)
                
                if not date_text:
                    continue
                
                # Obtener la fila completa
                row = date_element.find_element(By.XPATH, "./parent::tr")
                
                # Verificar si es una fila deseada
                row_class = row.get_attribute("class") or ""
                if any(c in row_class for c in ["thead", "divider", "spacer", "over_header"]):
                    continue
                
                # Crear datos para este partido
                match_data = {
                    "partido": str(match_id),
                    "Date": date_text
                }
                
                # Extraer el resto de campos
                for campo, data_stat in CAMPO_A_DATA_STAT.items():
                    if campo == "Date":  # Ya lo tenemos
                        continue
                    
                    try:
                        cell = row.find_element(By.XPATH, f".//td[@data-stat='{data_stat}']")
                        match_data[campo] = cell.text.strip()
                    except:
                        match_data[campo] = ""
                
                matches_data.append(match_data)
                match_id += 1
    
    except Exception as e:
        print(f"Error en extracción principal: {e}")
        print(traceback.format_exc())
    
    # Si aún no tenemos datos, intentar con JavaScript
    if not matches_data:
        try:
            print("Intentando extracción con JavaScript...")
            
            js_script = """
            function extractFBrefMatches() {
                var matches = [];
                var matchId = 1;
                
                // Definir mapeo de data-stat a campos
                var dataStatMap = {
                    "date": "Date",
                    "dayofweek": "Day",
                    "comp": "Comp",
                    "round": "Round",
                    "venue": "Venue",
                    "result": "Result",
                    "team": "Squad",
                    "opponent": "Opponent",
                    "game_started": "Start",
                    "position": "Pos",
                    "minutes": "Min",
                    "goals": "Gls",
                    "assists": "Ast",
                    "pens_made": "PK",
                    "pens_att": "PKatt",
                    "shots": "Sh",
                    "shots_on_target": "SoT",
                    "cards_yellow": "CrdY",
                    "cards_red": "CrdR",
                    "fouls": "Fls",
                    "fouled": "Fld",
                    "offsides": "Off",
                    "crosses": "Crs",
                    "tackles_won": "TklW",
                    "interceptions": "Int",
                    "own_goals": "OG",
                    "pens_won": "PKwon",
                    "pens_conceded": "PKcon"
                };
                
                // Buscar todas las celdas de fecha con atributo csk
                var dateCells = document.querySelectorAll('th[data-stat="date"][csk], td[data-stat="date"][csk]');
                
                for (var i = 0; i < dateCells.length; i++) {
                    var dateCell = dateCells[i];
                    var cskDate = dateCell.getAttribute('csk');
                    
                    if (!cskDate) continue;
                    
                    // Formatear la fecha
                    var formattedDate = cskDate;
                    if (cskDate.length === 8) {
                        formattedDate = cskDate.substr(0, 4) + '-' + cskDate.substr(4, 2) + '-' + cskDate.substr(6, 2);
                    }
                    
                    var row = dateCell.parentNode;
                    
                    // Verificar si es una fila válida
                    if (!row || row.classList.contains('thead') || 
                        row.classList.contains('divider') || 
                        row.classList.contains('spacer') || 
                        row.classList.contains('over_header')) {
                        continue;
                    }
                    
                    var match = {
                        partido: matchId.toString(),
                        Date: formattedDate
                    };
                    
                    // Extraer el resto de campos
                    for (var stat in dataStatMap) {
                        if (stat === 'date') continue; // Ya tenemos la fecha
                        
                        var cell = row.querySelector('td[data-stat="' + stat + '"]');
                        if (cell) {
                            match[dataStatMap[stat]] = cell.textContent.trim();
                        } else {
                            match[dataStatMap[stat]] = "";
                        }
                    }
                    
                    matches.push(match);
                    matchId++;
                }
                
                // Si no encontramos nada con csk, intentar con los enlaces
                if (matches.length === 0) {
                    var dateLinks = document.querySelectorAll('td[data-stat="date"] a');
                    
                    for (var i = 0; i < dateLinks.length; i++) {
                        var link = dateLinks[i];
                        var href = link.getAttribute('href');
                        var dateMatch = href.match(/(\\d{4}-\\d{2}-\\d{2})/);
                        
                        if (!dateMatch) continue;
                        
                        var row = link.closest('tr');
                        
                        if (!row || row.classList.contains('thead') || 
                            row.classList.contains('divider') || 
                            row.classList.contains('spacer') || 
                            row.classList.contains('over_header')) {
                            continue;
                        }
                        
                        var match = {
                            partido: matchId.toString(),
                            Date: dateMatch[1]
                        };
                        
                        // Extraer el resto de campos
                        for (var stat in dataStatMap) {
                            if (stat === 'date') continue;
                            
                            var cell = row.querySelector('td[data-stat="' + stat + '"]');
                            if (cell) {
                                match[dataStatMap[stat]] = cell.textContent.trim();
                            } else {
                                match[dataStatMap[stat]] = "";
                            }
                        }
                        
                        matches.push(match);
                        matchId++;
                    }
                }
                
                return matches;
            }
            
            return extractFBrefMatches();
            """
            
            js_matches = driver.execute_script(js_script)
            print(f"Extracción JavaScript encontró {len(js_matches)} partidos")
            
            if js_matches and len(js_matches) > 0:
                matches_data = js_matches
        
        except Exception as js_e:
            print(f"Error en extracción JavaScript: {js_e}")
    
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
    
    # Resto de la limpieza de datos (como en la función original)
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
        
        # Convertir valores vacíos a "0" en campos numéricos
        numeric_fields = ["Gls", "Ast", "PK", "PKatt", "Sh", "SoT", "CrdY", "CrdR", 
                         "Fls", "Fld", "Off", "Crs", "TklW", "Int", "OG", "PKwon", "PKcon"]
        
        for field in numeric_fields:
            if field in partido:
                try:
                    if not partido[field] or not re.match(r'^\d+$', partido[field].strip()):
                        partido[field] = "0"
                except:
                    partido[field] = "0"
    
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
        
        # Nombre de archivo simplificado: solo año y nombre del jugador
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
    parser = argparse.ArgumentParser(description='Scraper especializado para partidos de FBref')
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
        print("\n=== Scraper especializado para FBref ===")
        url = input("Introduce la URL de la página del jugador (presiona Enter para usar URL predeterminada): ")
        
        if not url:
            url = "https://fbref.com/en/players/09a9e921/matchlogs/2024/Carlos-Bacca-Match-Logs"
            print(f"Usando URL predeterminada: {url}")
    
    # Información del proceso
    print("\n=== Información del scraper ===")
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
    print("- Verifica que la URL sea correcta")
    print("- Aumenta el tiempo de espera (--timeout)")
    print("- Prueba con navegador visible (--visible)")
    print("- Intenta con otro navegador (--browser chrome)")

if __name__ == "__main__":
    main()