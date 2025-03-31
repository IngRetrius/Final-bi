import time
import datetime
import argparse
import os
# Importar TODAS las funciones necesarias
from sofascore_scraper import main as run_scraper

if __name__ == "__main__":
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Scraper de SofaScore para la Liga Colombiana')
    parser.add_argument('--visible', action='store_true', 
                        help='Ejecutar con navegador visible (no headless)')
    
    args = parser.parse_args()
    
    # Solicitar tipo de torneo (Apertura o Clausura)
    tournament_type = ""
    while tournament_type not in ["1", "2"]:
        tournament_type = input("Selecciona el torneo (1: Apertura, 2: Clausura): ")
        if tournament_type not in ["1", "2"]:
            print("Opción inválida. Por favor, selecciona 1 para Apertura o 2 para Clausura.")
    
    # Determinar URLs y nombres basados en la selección
    if tournament_type == "1":
        tournament_name = "Apertura"
        tournament_url = "https://www.sofascore.com/tournament/football/colombia/primera-a-apertura/11539"
    else:
        tournament_name = "Clausura"
        tournament_url = "https://www.sofascore.com/tournament/football/colombia/primera-a-clausura/11536"
    
    # Solicitar ID del torneo (año)
    tournament_id = input(f"Introduce el ID de {tournament_name} (por ejemplo, 70681 para 2025): ")
    if not tournament_id:
        tournament_id = "70681" if tournament_type == "1" else "63819"  # Valores predeterminados
    
    # Iniciar cronómetro
    start_time = time.time()
    print(f"Iniciando scraper a las {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar scraper pasando los parámetros
    run_scraper(visible=args.visible, tournament_type=tournament_name, tournament_url=tournament_url, tournament_id=tournament_id)
    
    # Mostrar tiempo de ejecución
    elapsed_time = time.time() - start_time
    print(f"\nProceso completado en {elapsed_time:.2f} segundos.")