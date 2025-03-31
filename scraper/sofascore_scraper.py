"""
Scraper para SofaScore usando Firefox, optimizado para extraer estadísticas de jugadores
de la Liga Colombiana Primera A
"""

import time
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import traceback
import re
from config import *

def create_firefox_driver(visible=True):
    """
    Crea y configura el driver de Firefox
    
    Args:
        visible (bool): Si es False, se ejecuta en modo headless
    
    Returns:
        webdriver: El driver de Firefox configurado
    """
    print("Configurando el navegador Firefox...")
    options = FirefoxOptions()
    if not visible:
        options.add_argument("--headless")
    
    # Configurar user agent para evitar detección
    options.set_preference("general.useragent.override", HEADERS["User-Agent"])
    
    # Desactivar notificaciones y otras opciones que pueden interferir
    options.set_preference("dom.webnotifications.enabled", False)
    options.set_preference("dom.push.enabled", False)
    
    try:
        driver = webdriver.Firefox(options=options)
        print("Firefox inicializado correctamente")
        return driver
    except Exception as e:
        print(f"Error al inicializar Firefox: {e}")
        raise

def navigate_to_tournament_page(driver):
    """
    Navega a la página principal del torneo
    
    Args:
        driver: El driver de Selenium
    
    Returns:
        bool: True si la navegación fue exitosa, False en caso contrario
    """
    try:
        # Navegar directamente a la URL del torneo con ID específico
        full_url = f"{TOURNAMENT_URL}#id:{TOURNAMENT_ID}"
        driver.get(full_url)
        print(f"Navegando a: {full_url}")
        time.sleep(8)  # Esperar a que la página cargue completamente
        
        # Verificar si hay un banner de cookies y cerrarlo
        try:
            cookie_button = driver.find_element(By.XPATH, 
                "//button[contains(text(), 'Accept') or contains(text(), 'Aceptar')]")
            cookie_button.click()
            print("Banner de cookies cerrado")
            time.sleep(1)
        except:
            print("No se encontró banner de cookies o ya fue aceptado")
        
        print(f"Título de la página: {driver.title}")
        
        return True
            
    except Exception as e:
        print(f"Error al navegar a la página del torneo: {e}")
        print(traceback.format_exc())
        return False

def find_player_statistics_section(driver):
    """
    Encuentra la sección de estadísticas de jugadores
    
    Args:
        driver: El driver de Selenium
    
    Returns:
        bool: True si encontró la sección, False en caso contrario
    """
    try:
        # Buscar el encabezado "Player statistics"
        try:
            stats_header = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, 
                    "//div[contains(text(), 'Player statistics') or contains(text(), 'Estadísticas de jugador')]"))
            )
            print(f"Sección de estadísticas de jugadores encontrada: '{stats_header.text}'")
            return True
        except TimeoutException:
            print("No se encontró el encabezado de estadísticas de jugadores mediante texto")
        
        # Intentar buscar la sección por su estructura
        try:
            # Buscar tabs de estadísticas (Summary, Attack, Defence, etc.)
            stats_tabs = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Summary') or contains(text(), 'Attack') or contains(text(), 'Defence')]")
            
            if stats_tabs:
                print(f"Encontrados {len(stats_tabs)} tabs de estadísticas")
                return True
        except:
            print("No se encontraron tabs de estadísticas")
        
        # Intentar encontrar la tabla directamente
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            if tables:
                print(f"Se encontraron {len(tables)} tablas en la página")
                return True
        except:
            print("No se encontraron tablas en la página")
        
        print("No se pudo encontrar claramente la sección de estadísticas de jugadores")
        return False
        
    except Exception as e:
        print(f"Error al buscar sección de estadísticas: {e}")
        return False

def select_statistics_tab(driver, tab_name):
    """
    Selecciona una pestaña específica de estadísticas (Summary, Attack, Defence, etc.)
    usando JavaScript para evitar problemas de elementos superpuestos
    
    Args:
        driver: El driver de Selenium
        tab_name: Nombre de la pestaña a seleccionar
    
    Returns:
        bool: True si seleccionó la pestaña, False en caso contrario
    """
    try:
        # Usar JavaScript para encontrar y hacer clic en la pestaña
        script = f"""
        // Intentar por data-tabid
        var tabBtn = document.querySelector('button[data-tabid="{tab_name}"]');
        if (tabBtn) {{
            arguments[0].scrollIntoView(true);
            arguments[0].click();
            return true;
        }}
        
        // Buscar cualquier botón tipo Chip que contenga el texto
        var buttons = document.querySelectorAll('button.Chip');
        for (var i = 0; i < buttons.length; i++) {{
            var btn = buttons[i];
            if (btn.textContent.toLowerCase().includes('{tab_name.lower()}')) {{
                arguments[1].scrollIntoView(true);
                // Ejecutar el evento de clic directamente, evitando el clic normal
                var clickEvent = document.createEvent('Events');
                clickEvent.initEvent('click', true, false);
                arguments[1].dispatchEvent(clickEvent);
                return true;
            }}
        }}
        
        return false;
        """
        
        # Obtener todos los botones tipo Chip para pasarlos como argumentos
        tab_button = None
        try:
            tab_button = driver.find_element(By.CSS_SELECTOR, f"button[data-tabid='{tab_name}']")
        except:
            pass
        
        chip_buttons = driver.find_elements(By.CSS_SELECTOR, "button.Chip")
        target_button = None
        
        for btn in chip_buttons:
            if tab_name.lower() in btn.text.lower():
                target_button = btn
                break
        
        # Ejecutar el script con los botones como argumentos
        if tab_button or target_button:
            result = driver.execute_script(script, tab_button or chip_buttons[0], target_button or chip_buttons[0])
            if result:
                print(f"Pestaña '{tab_name}' seleccionada usando JavaScript")
                time.sleep(2)  # Esperar a que cargue la tabla
                return True
        
        # Método alternativo - forzar el clic con JavaScript
        alt_script = f"""
        var allButtons = Array.from(document.querySelectorAll('button'));
        var targetButton = allButtons.find(b => 
            b.textContent.toLowerCase().includes('{tab_name.lower()}') || 
            b.getAttribute('data-tabid') === '{tab_name}' ||
            b.getAttribute('aria-label') && b.getAttribute('aria-label').toLowerCase().includes('{tab_name.lower()}')
        );
        
        if (targetButton) {{
            // Forzar un clic con JavaScript ignorando cualquier obstáculo
            var clickEvent = document.createEvent('MouseEvents');
            clickEvent.initEvent('click', true, true);
            targetButton.dispatchEvent(clickEvent);
            return true;
        }}
        
        return false;
        """
        
        result = driver.execute_script(alt_script)
        if result:
            print(f"Pestaña '{tab_name}' seleccionada usando JavaScript alternativo")
            time.sleep(2)
            return True
        
        print(f"No se pudo seleccionar la pestaña '{tab_name}' con ningún método")
        return False
        
    except Exception as e:
        print(f"Error al seleccionar pestaña '{tab_name}': {e}")
        print(traceback.format_exc())
        return False

def extract_player_table(driver):
    """
    Extrae los datos de la tabla de jugadores
    
    Args:
        driver: El driver de Selenium
        
    Returns:
        list: Lista de diccionarios con datos de jugadores
    """
    try:
        # Esperar a que la tabla esté presente
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        print("Tabla de jugadores encontrada")
        
        # Extraer encabezados de la tabla
        headers = []
        header_cells = table.find_elements(By.XPATH, ".//th")
        
        for cell in header_cells:
            text = cell.text.strip()
            if text and text != "#":
                headers.append(text)
        
        print(f"Encabezados encontrados: {headers}")
        
        # Extraer filas de jugadores
        rows = table.find_elements(By.XPATH, ".//tbody/tr")
        print(f"Filas de jugadores encontradas: {len(rows)}")
        
        # Extraer datos
        players_data = []
        
        for row in rows:
            cells = row.find_elements(By.XPATH, "./td")
            
            if len(cells) > 1:
                player = {}
                
                # Obtener número de posición
                try:
                    player["Position"] = cells[0].text.strip()
                except:
                    player["Position"] = ""
                
                # Recorrer todas las celdas para buscar atributos title y clasificarlos correctamente
                team_name = None
                player_name = None
                titles = []
                
                # Primero recopilamos todos los atributos title
                for cell in cells:
                    try:
                        title = cell.get_attribute("title")
                        if title and len(title) > 2:
                            # Eliminamos la impresión de cada título encontrado
                            titles.append(title)
                    except:
                        pass
                
                # Si tenemos exactamente dos títulos, es muy probable que sean equipo y jugador
                if len(titles) >= 2:
                    # Heurística: Si un título contiene espacio, probablemente es un nombre de jugador
                    # Si no contiene espacio o tiene pocas palabras, probablemente es un equipo
                    
                    # Ordenamos los títulos por número de palabras (menos a más)
                    sorted_titles = sorted(titles, key=lambda x: len(x.split()))
                    
                    # El primero probablemente es el equipo, el último probablemente es el jugador
                    # (pero verificamos más condiciones)
                    for title in titles:
                        # Si contiene palabras como FC, Independiente, Atlético, etc., es un equipo
                        team_indicators = ["FC", "Independiente", "Atlético", "Deportivo", "Junior", "Caldas",
                                         "Santa Fe", "Magdalena", "Medellín", "Cali", "Nacional", "Bucaramanga",
                                         "Chicó", "Tolima", "Millonarios", "Fortaleza", "Águilas", "Envigado",
                                         "Alianza", "Pasto", "Equidad", "Pereira", "Rionegro", "Llaneros",
                                         "Unión", "América", "Barranquilla", "Valledupar", "Doradas", "CEIF"]
                        
                        # Verificar si contiene alguno de los indicadores de equipo
                        if any(indicator in title for indicator in team_indicators):
                            team_name = title
                        # Si tiene espacios y no se ha identificado como jugador, probablemente es un jugador
                        elif ' ' in title and not player_name:
                            player_name = title
                
                # Si no pudimos identificar claramente, usemos la heurística simple
                if not team_name or not player_name:
                    # Si tenemos al menos dos títulos
                    if len(titles) >= 2:
                        # Ordenamos por número de palabras
                        titles_by_words = sorted(titles, key=lambda x: len(x.split()))
                        # El que tiene menos palabras probablemente es el equipo
                        team_name = titles_by_words[0]
                        # El que tiene más palabras probablemente es el jugador
                        player_name = titles_by_words[-1]
                    # Si solo tenemos un título, intentamos adivinar
                    elif len(titles) == 1:
                        if ' ' in titles[0]:
                            # Si tiene espacio, probablemente es un jugador
                            player_name = titles[0]
                        else:
                            # Si no tiene espacio, probablemente es un equipo
                            team_name = titles[0]
                
                # Asignar los valores encontrados
                if team_name:
                    player["Team"] = team_name
                else:
                    player["Team"] = "Unknown"
                
                if player_name:
                    player["Name"] = player_name
                else:
                    player["Name"] = "Unknown"
                
                # Extraer estadísticas usando los encabezados correctos
                # Primero identificamos cuáles son las columnas de estadísticas (no Team o Name)
                stat_headers = [h for h in headers if h != "Team" and h != "Name"]
                
                # Las estadísticas están en celdas después de las columnas de Team y Name
                # En SofaScore, después de Position, suelen estar Team, Name y luego las estadísticas
                for i, header in enumerate(stat_headers):
                    # Comenzar desde la celda 3 (índice 2) para las estadísticas
                    cell_idx = 3 + i
                    if cell_idx < len(cells):
                        player[header] = cells[cell_idx].text.strip()
                
                # Validar y corregir
                if player["Team"] == player["Name"]:
                    # Si son iguales, algo está mal. Intentemos usar heurística
                    if ' ' in player["Team"]:
                        # Si tiene espacio, probablemente es un jugador
                        player["Name"] = player["Team"]
                        player["Team"] = "Unknown"
                
                # Verificación final por consistencia
                if "Name" in player and player["Name"] != "Unknown" and "Team" in player and player["Team"] != "Unknown":
                    # VERIFICACIÓN FINAL: Asegurarnos de que equipo y jugador no están invertidos
                    # Indicadores de equipos (palabras que suelen estar en nombres de equipos)
                    team_indicators = ["FC", "Independiente", "Atlético", "Deportivo", "Junior", "Caldas",
                                       "Santa Fe", "Magdalena", "Medellín", "Cali", "Nacional", "Bucaramanga",
                                       "Chicó", "Tolima", "Millonarios", "Fortaleza", "Águilas", "Envigado",
                                       "Alianza", "Pasto", "Equidad", "Pereira", "Rionegro", "Llaneros",
                                       "Unión", "América", "Barranquilla", "Valledupar", "Doradas", "CEIF"]
                    
                    # Si el "nombre" contiene alguno de estos indicadores, podría ser un equipo
                    if any(indicator in player["Name"] for indicator in team_indicators):
                        # Y si el "equipo" tiene espacios (como un nombre), probablemente están invertidos
                        if ' ' in player["Team"] and len(player["Team"].split()) > 1:
                            # Intercambiar valores
                            player["Team"], player["Name"] = player["Name"], player["Team"]
                            # Eliminamos la impresión de corrección de inversión
                
                # Eliminamos la impresión de cada jugador añadido
                players_data.append(player)
        
        print(f"Extraídos datos de {len(players_data)} jugadores")
        return players_data
        
    except TimeoutException:
        print("No se pudo encontrar la tabla de jugadores")
        return []
    except Exception as e:
        print(f"Error al extraer datos de la tabla: {e}")
        print(traceback.format_exc())
        return []

def navigate_pagination(driver, page_num):
    """
    Navega a una página específica de la paginación
    
    Args:
        driver: El driver de Selenium
        page_num: Número de página a navegar
    
    Returns:
        bool: True si navegó correctamente, False en caso contrario
    """
    try:
        # Método 1: Buscar el botón de la página por su texto exacto
        try:
            page_button = driver.find_element(By.XPATH, f"//button[text()='{page_num}']")
            driver.execute_script("arguments[0].scrollIntoView(true);", page_button)
            time.sleep(0.5)
            page_button.click()
            print(f"Navegando a la página {page_num}")
            time.sleep(3)  # Esperar a que cargue la tabla
            return True
        except NoSuchElementException:
            print(f"No se encontró el botón exacto para la página {page_num}, intentando otros métodos")
        
        # Método 2: Buscar botones con clase "button" que tengan el texto del número de página
        try:
            page_buttons = driver.find_elements(By.CSS_SELECTOR, "button.button")
            for btn in page_buttons:
                if btn.text.strip() == str(page_num):
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(0.5)
                    btn.click()
                    print(f"Navegando a la página {page_num} mediante botón de clase 'button'")
                    time.sleep(3)
                    return True
        except:
            print(f"Error al buscar botones con clase 'button' para la página {page_num}")
        
        # Método 3: Buscar cualquier botón que contenga solo el número de página
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.text.strip() == str(page_num):
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(0.5)
                    btn.click()
                    print(f"Navegando a la página {page_num} mediante botón genérico")
                    time.sleep(3)
                    return True
        except:
            print(f"Error al buscar botones genéricos para la página {page_num}")
        
        # Método 4: JavaScript directo para encontrar y hacer clic en el botón por su texto
        script = f"""
        var buttons = document.querySelectorAll('button');
        for (var i = 0; i < buttons.length; i++) {{
            if (buttons[i].textContent.trim() === '{page_num}') {{
                buttons[i].click();
                return true;
            }}
        }}
        return false;
        """
        
        result = driver.execute_script(script)
        if result:
            print(f"Navegando a la página {page_num} mediante JavaScript")
            time.sleep(3)
            return True
        
        print(f"No se pudo encontrar el botón para la página {page_num} con ningún método")
        return False
        
    except Exception as e:
        print(f"Error al navegar a la página {page_num}: {e}")
        print(traceback.format_exc())
        return False

def click_next_page_button(driver):
    """
    Hace clic en el botón de siguiente página
    
    Args:
        driver: El driver de Selenium
    
    Returns:
        bool: True si navegó a la siguiente página, False en caso contrario
    """
    try:
        # Método 1: Intentar encontrar botones de navegación por número específico
        current_page = None
        try:
            # Encontrar un botón que tenga una clase que indique que es la página actual
            current_page_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(@class, 'filled') or contains(@class, 'active') or contains(@class, 'selected')]")
            
            for btn in current_page_buttons:
                if btn.text.isdigit():
                    current_page = int(btn.text)
                    print(f"Página actual detectada: {current_page}")
                    break
        except:
            print("No se pudo detectar la página actual")
        
        # Si sabemos la página actual, intentar hacer clic en la siguiente página por número
        if current_page:
            next_page = current_page + 1
            try:
                next_page_button = driver.find_element(By.XPATH, f"//button[text()='{next_page}']")
                next_page_button.click()
                print(f"Navegando a la página {next_page}")
                time.sleep(3)
                return True
            except NoSuchElementException:
                print(f"No se encontró botón para la página {next_page}")
                # Si no encontramos el botón por número, continuamos con otros métodos
        
        # Método 2: Buscar botón por contenido SVG (como se ve en la imagen)
        svg_buttons = driver.find_elements(By.XPATH, "//button[.//svg]")
        
        if svg_buttons:
            print(f"Encontrados {len(svg_buttons)} botones con SVG")
            
            # Recorrer todos los botones con SVG
            for btn in svg_buttons:
                # Verificar si parece ser un botón de "siguiente"
                btn_class = btn.get_attribute("class")
                btn_html = btn.get_attribute("innerHTML")
                
                # Intentar identificar si es un botón "siguiente" basado en la posición o forma
                is_next_button = False
                
                # Si tiene path dentro del SVG, podría ser una flecha
                if "path" in btn_html.lower() or "svg" in btn_html.lower():
                    is_next_button = True
                
                # Si está a la derecha de los botones de número
                position = btn.location.get('x', 0)
                if position > 500:  # Asumiendo que los botones de número están en la izquierda
                    is_next_button = True
                
                if is_next_button:
                    # Verificar si el botón está deshabilitado
                    if btn.get_attribute("disabled") == "true":
                        print("Botón de siguiente página detectado pero está deshabilitado (última página)")
                        return False
                    
                    # Desplazarse para asegurarse de que el botón sea visible
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(0.5)
                    
                    # Hacer clic en el botón
                    btn.click()
                    print("Navegando a la siguiente página mediante botón SVG")
                    time.sleep(3)
                    return True
        
        # Método 3: Buscar por botones específicos visibles en la captura de pantalla
        try:
            # Buscar elemento específico con svg-wrapper
            arrow_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(.//svg/@class, 'wrapper') or .//svg/@width='24']")
            
            if arrow_buttons:
                print(f"Encontrados {len(arrow_buttons)} botones específicos de flecha")
                # Tomar el último que suele ser el "siguiente"
                next_btn = arrow_buttons[-1]
                
                # Verificar si está deshabilitado
                if next_btn.get_attribute("disabled") == "true":
                    print("Botón específico de flecha está deshabilitado (última página)")
                    return False
                
                # Desplazarse y hacer clic
                driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                time.sleep(0.5)
                next_btn.click()
                print("Navegando a la siguiente página mediante botón específico")
                time.sleep(3)
                return True
        except Exception as e:
            print(f"Error al intentar método específico de navegación: {e}")
        
        # Método 4: Intentar JavaScript directo para encontrar y hacer clic en el botón
        try:
            script = """
            // Buscar botones de navegación
            var buttons = document.querySelectorAll('button');
            var nextButton = null;
            
            // Encontrar el botón que contiene SVG y está más a la derecha
            var maxX = 0;
            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                if (btn.querySelector('svg') && !btn.disabled) {
                    var rect = btn.getBoundingClientRect();
                    if (rect.x > maxX) {
                        maxX = rect.x;
                        nextButton = btn;
                    }
                }
            }
            
            if (nextButton) {
                nextButton.click();
                return true;
            }
            
            return false;
            """
            
            result = driver.execute_script(script)
            if result:
                print("Navegando a la siguiente página mediante JavaScript")
                time.sleep(3)
                return True
        except Exception as e:
            print(f"Error al ejecutar script de navegación: {e}")
        
        print("No se pudo encontrar un método válido para navegar a la siguiente página")
        return False
        
    except Exception as e:
        print(f"Error al navegar a la siguiente página: {e}")
        print(traceback.format_exc())
        return False

def save_data(data, category):
    """
    Guarda los datos en un archivo CSV
    
    Args:
        data: Lista de diccionarios con datos de jugadores
        category: Categoría de los datos (para el nombre del archivo)
    
    Returns:
        DataFrame: DataFrame con los datos guardados
    """
    if not data:
        print(f"No hay datos para guardar de la categoría {category}")
        return None
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    # Crear carpeta si no existe
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    
    # Guardar archivo
    file_path = os.path.join(DATA_FOLDER, INDIVIDUAL_STATS_FILES[category])
    df.to_csv(file_path, index=False)
    print(f"Datos guardados en {file_path}")
    
    return df

def scrape_category_data(driver, category):
    """
    Extrae datos de todas las páginas para una categoría específica
    
    Args:
        driver: El driver de Selenium
        category: Categoría de estadísticas a extraer
    
    Returns:
        list: Lista combinada de datos de todas las páginas
    """
    # Seleccionar la pestaña de la categoría (excepto summary que ya está seleccionada por defecto)
    if category != "summary":
        if not select_statistics_tab(driver, category):
            print(f"No se pudo seleccionar la categoría {category}, saltando...")
            return []
    
    all_data = []
    
    # Extraer datos de la primera página
    page_data = extract_player_table(driver)
    if page_data:
        all_data.extend(page_data)
        print(f"Extraídos {len(page_data)} jugadores de la página 1")
    
    # Extraer datos de las siguientes páginas
    page_num = 1
    max_pages = 30  # Limitar a 10 páginas para evitar problemas
    
    while page_num < max_pages:
        # Intentar ir a la siguiente página
        if click_next_page_button(driver):
            page_num += 1
            print(f"Procesando página {page_num}")
            
            # Extraer datos de la página actual
            page_data = extract_player_table(driver)
            if page_data:
                all_data.extend(page_data)
                print(f"Extraídos {len(page_data)} jugadores de la página {page_num}")
            else:
                print(f"No se pudieron extraer datos de la página {page_num}")
                break
        else:
            print(f"No se pudo navegar a la página siguiente, finalizando")
            break
    
    print(f"Total de {len(all_data)} jugadores extraídos para la categoría {category}")
    return all_data

def scrape_all_categories(driver):
    """
    Extrae datos de todas las categorías de estadísticas
    
    Args:
        driver: El driver de Selenium
    
    Returns:
        dict: Diccionario con DataFrames por categoría
    """
    all_data = {}
    
    # Mapeo de categorías a nombres de pestañas en la interfaz
    tab_mapping = {
        "summary": "summary",
        "attack": "attack",
        "defence": "defence",
        "passing": "passing",
        "goalkeeper": "goalkeeper",
        "detailed": "detailed"
    }
    
    # Extraer datos para cada categoría
    for category in STAT_CATEGORIES:
        print(f"\nExtrayendo estadísticas de la categoría: {category}")
        tab_name = tab_mapping.get(category, category)
        
        # Intentar seleccionar la pestaña (excepto summary que ya está seleccionada por defecto)
        if category == "summary" or select_statistics_tab(driver, tab_name):
            # Si es summary o se pudo seleccionar la pestaña, extraer datos
            category_data = scrape_category_data(driver, category)
            if category_data:
                category_df = save_data(category_data, category)
                all_data[category] = category_df
        else:
            print(f"No se pudo seleccionar la categoría {category}, saltando...")
    
    return all_data
   
def combine_data(all_data, output_file_path):
    """
    Combina los datos de todas las categorías
    
    Args:
        all_data (dict): Diccionario con DataFrames por categoría
        output_file_path (str): Ruta donde guardar el archivo combinado
    
    Returns:
        DataFrame: DataFrame combinado con todos los datos
    """
    print("Combinando datos de todas las categorías...")
    
    # Verificar si hay datos para combinar
    has_data = False
    for df in all_data.values():
        if df is not None and not df.empty:
            has_data = True
            break
    
    if not has_data:
        print("No hay datos suficientes para combinar")
        return None
    
    # Buscar la primera categoría con datos
    base_df = None
    for category in STAT_CATEGORIES:
        if category in all_data and all_data[category] is not None and not all_data[category].empty:
            base_df = all_data[category]
            print(f"Usando datos de '{category}' como base")
            break
    
    if base_df is None:
        print("No se encontró ninguna categoría con datos")
        return None
    
    # Identificar columnas para combinar (clave primaria)
    key_columns = []
    if "Name" in base_df.columns:
        key_columns.append("Name")
    if "Team" in base_df.columns:
        key_columns.append("Team")
    if "Position" in base_df.columns:
        key_columns.append("Position")  # Añadir posición como parte de la clave
    
    if not key_columns:
        print("No se encontraron columnas clave para combinar")
        return None
    
    # Eliminar duplicados en el DataFrame base antes de combinar
    base_df = base_df.drop_duplicates(subset=key_columns)
    print(f"DataFrame base tiene {len(base_df)} registros únicos")
    
    # Combinar datos
    combined_df = base_df.copy()
    
    for category, df in all_data.items():
        if df is not None and not df.empty and not df.equals(base_df):
            # Verificar que las columnas clave existen
            if all(col in df.columns for col in key_columns):
                # Primero eliminar duplicados en el DataFrame a combinar
                df = df.drop_duplicates(subset=key_columns)
                print(f"DataFrame de '{category}' tiene {len(df)} registros únicos")
                
                # Eliminar columnas duplicadas
                overlap_cols = [c for c in df.columns if c in combined_df.columns and c not in key_columns]
                merge_df = df.drop(columns=overlap_cols, errors='ignore')
                
                # Combinar con merge outer para no perder datos
                try:
                    combined_df = pd.merge(combined_df, merge_df, on=key_columns, how='outer')
                    print(f"Datos de '{category}' combinados")
                    
                    # Verificar duplicados después del merge
                    combined_df = combined_df.drop_duplicates(subset=key_columns)
                    print(f"Después de combinar con '{category}', hay {len(combined_df)} registros")
                except Exception as e:
                    print(f"Error al combinar datos de '{category}': {e}")
            else:
                print(f"No se pudieron combinar datos de '{category}' (faltan columnas clave)")
    
    # Eliminar duplicados finales
    combined_df = combined_df.drop_duplicates(subset=key_columns)
    print(f"DataFrame final tiene {len(combined_df)} registros únicos")
    
    # Guardar archivo combinado
    if combined_df is not None and not combined_df.empty:
        combined_df.to_csv(output_file_path, index=False)
        print(f"Datos combinados guardados en {output_file_path}")
    
    return combined_df

def main(visible=True, tournament_type="Apertura", tournament_url=TOURNAMENT_URL, tournament_id="70681"):
    """
    Función principal
    
    Args:
        visible (bool): Si es True, el navegador será visible, si es False, se ejecuta en modo headless
        tournament_type (str): Tipo de torneo (Apertura o Clausura)
        tournament_url (str): URL del torneo
        tournament_id (str): ID del torneo a scrapear
    """
    # Actualizar la configuración del torneo
    global TOURNAMENT_URL, TOURNAMENT_ID
    TOURNAMENT_URL = tournament_url
    TOURNAMENT_ID = tournament_id
    
    print(f"Iniciando scraper Firefox para {tournament_type} {TOURNAMENT_ID}")
    start_time = time.time()
    
    # Crear la estructura de carpetas
    folder_name = f"{tournament_type.lower()}_{TOURNAMENT_ID}"
    data_folder = os.path.join(DATA_FOLDER, folder_name)
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        print(f"Creada carpeta para el torneo: {data_folder}")
    
    # Inicializar driver Firefox con el parámetro de visibilidad
    driver = create_firefox_driver(visible=visible)
    
    try:
        # Establecer tiempos de espera
        driver.set_page_load_timeout(60)  # 60 segundos para cargar la página
        
        # Navegar a la página del torneo
        if not navigate_to_tournament_page(driver):
            print("No se pudo navegar a la página del torneo, abortando.")
            return
        
        # Encontrar la sección de estadísticas de jugadores
        if not find_player_statistics_section(driver):
            print("No se pudo encontrar la sección de estadísticas de jugadores, pero continuaremos.")
        
        # Definir los modos y preguntar al usuario si desea continuar después de cada uno
        accumulation_modes = ["All", "Per 90 mins"]
        
        for acc_mode in accumulation_modes:
            if acc_mode == "Per 90 mins":
                # Pedir al usuario que cambie manualmente el modo
                user_input = ""
                while user_input.lower() not in ["s", "n"]:
                    print("\n==========================================")
                    print("Extracción en modo 'All' completada.")
                    print("1. Por favor, cambia manualmente a modo 'Per 90 mins' en el navegador.")
                    print("   (Haz clic en el dropdown 'All' y selecciona 'Per 90 mins')")
                    print("2. Cuando hayas cambiado el modo, escribe 's' para continuar")
                    print("   o 'n' para terminar sin extraer datos de 'Per 90 mins'")
                    print("==========================================")
                    user_input = input("¿Continuar con la extracción en modo 'Per 90 mins'? (s/n): ")
                
                if user_input.lower() != "s":
                    print("Omitiendo extracción en modo 'Per 90 mins'")
                    break
            
            print(f"\n=== Extrayendo datos en modo: {acc_mode} ===\n")
            
            # Crear subcarpeta para este modo de acumulación
            mode_folder = os.path.join(data_folder, acc_mode.replace(" ", "_").lower())
            if not os.path.exists(mode_folder):
                os.makedirs(mode_folder)
            
            # Actualizar rutas de archivos para este modo
            file_paths = {}
            for category, filename in INDIVIDUAL_STATS_FILES.items():
                file_paths[category] = os.path.join(mode_folder, filename)
            
            player_data_file = os.path.join(mode_folder, PLAYER_DATA_FILE)
            
            # Extraer datos de todas las categorías para este modo
            all_data = {}
            
            for category in STAT_CATEGORIES:
                print(f"\nExtrayendo estadísticas de la categoría: {category} en modo {acc_mode}")
                # Si es summary o se pudo seleccionar la pestaña, extraer datos
                if category == "summary" or select_statistics_tab(driver, category):
                    category_data = scrape_category_data(driver, category)
                    if category_data:
                        file_path = file_paths[category]
                        df = pd.DataFrame(category_data)
                        df.to_csv(file_path, index=False)
                        print(f"Datos guardados en {file_path}")
                        
                        all_data[category] = df
                else:
                    print(f"No se pudo seleccionar la categoría {category}, saltando...")
            
            # Combinar todos los datos para este modo
            combined_df = combine_data(all_data, player_data_file)
            
            # Verificar si se han extraído correctamente los equipos
            if combined_df is not None and not combined_df.empty:
                teams_count = combined_df["Team"].nunique()
                unknown_count = combined_df[combined_df["Team"] == "Unknown"].shape[0] if "Unknown" in combined_df["Team"].values else 0
                
                print(f"\nEstadísticas de extracción para modo {acc_mode}:")
                print(f"- Total de filas: {combined_df.shape[0]}")
                print(f"- Equipos únicos encontrados: {teams_count}")
                if unknown_count > 0:
                    print(f"- Jugadores sin equipo identificado: {unknown_count} ({unknown_count/combined_df.shape[0]*100:.2f}%)")
                
                # Imprimir muestra de los primeros 5 equipos encontrados
                unique_teams = combined_df["Team"].unique()[:5]
                print(f"- Muestra de equipos: {', '.join(unique_teams)}")
        
        elapsed_time = time.time() - start_time
        print(f"Proceso completado exitosamente en {elapsed_time:.2f} segundos.")
    
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        print(traceback.format_exc())
    
    finally:
        # Cerrar el navegador
        driver.quit()
        print("Navegador cerrado")

if __name__ == "__main__":
    main()