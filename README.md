# Colombian Soccer Players Analysis and Recommendation System

## Project Overview
This project extracts player statistics from SofaScore for the Colombian Primera A league using web scraping techniques. It collects data in both total (accumulated) and per 90 minute formats, allowing for comprehensive player analysis.

## Current Features
- Web scraping of player statistics from SofaScore for Colombian Primera A (Apertura/Clausura)
- Extraction of multiple statistical categories:
  - Summary statistics
  - Attack statistics
  - Defense statistics
  - Passing statistics
  - Goalkeeper statistics
- Support for different data accumulation modes:
  - Total stats (All)
  - Per 90 minutes stats
- Organization of data in CSV files by category and accumulation mode
- Ability to combine data across categories into a comprehensive dataset

## Data Collected
For each player, the system collects data such as:
- Goals, assists, and key passes
- Successful dribbles and tackles
- Accurate passes percentage
- Shots and goal conversion rate
- Goalkeeper statistics (saves, clean sheets, etc.)
- And many more statistical categories

## Dependencies
- Python 3.8+
- Selenium
- pandas
- Firefox WebDriver (geckodriver)

## Usage
```bash
# Run with visible browser (recommended for first-time use)
python main.py --visible

# Then follow the prompts to select:
# 1. Tournament type (Apertura/Clausura)
# 2. Tournament ID (e.g., 70681 for 2024 Apertura)
```

During execution, you will be prompted to manually change the view from "All" stats to "Per 90 mins" stats after the first phase of data collection is complete.

## Output
The script creates a directory structure organized by tournament and data mode:
```
data/
  └── apertura_70681/
      ├── all/
      │   ├── jugadores_resumen.csv
      │   ├── jugadores_ataque.csv
      │   ├── jugadores_defensa.csv
      │   ├── jugadores_pases.csv
      │   ├── jugadores_porteros.csv
      │   └── jugadores_liga_colombiana_completo.csv
      └── per_90_mins/
          ├── jugadores_resumen.csv
          ├── jugadores_ataque.csv
          ├── ...
```

## Future Development
This project is part of a larger system for soccer player analysis and recommendation in Colombian football. Future phases will include:
- Data cleaning and preprocessing
- Statistical analysis and player performance metrics
- Time series analysis of player performance
- Player recommendation system based on specific criteria
- Interactive dashboard for data visualization


## License
This project is licensed under the MIT License - see the LICENSE file for details.