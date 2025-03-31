"""
Configuración para el web scraper de SofaScore - Jugadores de la Liga Colombiana
Incluye todas las categorías de estadísticas disponibles en el sitio
"""

# URLs base
BASE_URL = "https://www.sofascore.com"
TOURNAMENT_URL = "https://www.sofascore.com/tournament/football/colombia/primera-a-apertura/11539"
TOURNAMENT_ID = "70681"  # ID de la temporada actual

# Pestañas de estadísticas disponibles
STAT_CATEGORIES = [
    "summary",
    "attack", 
    "defence", 
    "passing", 
    "goalkeeper"
]

# Carpeta para almacenamiento de datos
DATA_FOLDER = "data/"

# Headers para simular un navegador real (importante para evitar bloqueos)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": f"{BASE_URL}",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Tiempo de espera entre solicitudes para evitar ser bloqueado (en segundos)
REQUEST_DELAY = 3

# Diccionario con todas las estadísticas de jugadores a extraer por categoría
PLAYER_STATS = {
    # Estadísticas generales/resumen
    "summary": [
        "name",
        "team",
        "position",
        "goals",
        "tackles",
        "assists",
        "average_sofascore_rating"
    ],
    
    # Estadísticas de ataque
    "attack": [
        "goals",
        "big_chances_missed",
        "succ_dribbles",
        "total_shots",
        "shots_on_target",
        "conversion"
    ],
    
    # Estadísticas de defensa
    "defence": [
        "tackles",
        "interceptions", 
        "clearances",
        "errors_led_to_goal",
        "duels_won",
        "duels_won_percentage"
    ],
    
    # Estadísticas de pases
    "passing": [
        "big_chances_created",
        "assists",
        "accurate_passes",
        "accurate_passes_percentage",
        "accurate_long_balls",
        "key_passes"
    ],
    
    # Estadísticas de portero
    "goalkeeper": [
        "saves",
        "clean_sheet",
        "penalties_saved",
        "saves_from_inside_box",
        "conceded",
        "prevented"
    ]
}

# Cantidad de reintentos para solicitudes fallidas
MAX_RETRIES = 3

# Nombres de archivos de salida
PLAYER_DATA_FILE = "jugadores_liga_colombiana_completo.csv"
INDIVIDUAL_STATS_FILES = {
    "summary": "jugadores_resumen.csv",
    "attack": "jugadores_ataque.csv",
    "defence": "jugadores_defensa.csv",
    "passing": "jugadores_pases.csv",
    "goalkeeper": "jugadores_porteros.csv"
}