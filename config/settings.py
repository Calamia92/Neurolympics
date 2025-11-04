"""
Configuration centrale du projet Neurolympics
"""

import os
from pathlib import Path

# Dossiers du projet
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"

# Fichiers de données
DATA_FILES = {
    'athletes': RAW_DATA_DIR / "olympic_athletes.json",
    'hosts': RAW_DATA_DIR / "olympic_hosts.xml", 
    'medals': RAW_DATA_DIR / "olympic_medals.xlsx",
    'results': RAW_DATA_DIR / "olympic_results.html"
}

# Configuration base de données
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'neurolympics'),
    'username': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'url': os.getenv('DATABASE_URL', '')
}

# Tables de la base de données
DATABASE_TABLES = {
    'athletes': 'olympic_athletes',
    'hosts': 'olympic_hosts',
    'medals': 'olympic_medals', 
    'results': 'olympic_results'
}

# Configuration validation
VALIDATION_CONFIG = {
    'max_file_size_mb': 50,
    'sample_size_json': 1000,
    'max_missing_data_pct': 50,
    'required_columns': {
        'athletes': ['athlete_url', 'athlete_full_name'],
        'hosts': ['game_location', 'game_start_date'],
        'medals': ['discipline_title', 'medal_type', 'athlete_full_name'],
        'results': ['discipline_title', 'event_title']
    }
}

# Configuration transformation
TRANSFORM_CONFIG = {
    'output_dir': PROCESSED_DATA_DIR,
    'export_format': 'csv',
    'date_format': '%Y-%m-%d',
    'encoding': 'utf-8'
}