"""
Integration des donnees scrapees avec la base de donnees existante
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.connection import get_db_connection
from src.scraping.base_scraper import BaseScraper
import pandas as pd
from datetime import datetime
from pathlib import Path

class ScrapingDBIntegrator:
    """Classe pour integrer les donnees scrapees dans la base de donnees"""
    
    def __init__(self):
        self.db_conn = get_db_connection()
        self.scraped_data_dir = Path("data/scraped/processed")
        
    def create_scraped_tables(self):
        """Cree les tables pour les donnees scrapees"""
        
        tables_sql = {
            'scraped_athletes_2024': '''
                CREATE TABLE IF NOT EXISTS scraped_athletes_2024 (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    sport VARCHAR(100),
                    country VARCHAR(100),
                    age INTEGER,
                    birth_year INTEGER,
                    profile_url TEXT,
                    medals_info TEXT,
                    details TEXT,
                    type VARCHAR(50),
                    source VARCHAR(50),
                    scraped_at TIMESTAMP,
                    qualified_2024 BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, source)
                )
            ''',
            'scraped_sports_2024': '''
                CREATE TABLE IF NOT EXISTS scraped_sports_2024 (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    url TEXT,
                    source VARCHAR(50),
                    scraped_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, source)
                )
            ''',
            'scraping_log': '''
                CREATE TABLE IF NOT EXISTS scraping_log (
                    id SERIAL PRIMARY KEY,
                    scraper_name VARCHAR(50),
                    status VARCHAR(20),
                    records_count INTEGER,
                    error_message TEXT,
                    execution_time FLOAT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        }
        
        for table_name, sql in tables_sql.items():
            try:
                with self.db_conn.engine.connect() as conn:
                    # Utiliser text() pour executer SQL brut
                    from sqlalchemy import text
                    conn.execute(text(sql))
                    conn.commit()
                print(f"OK Table '{table_name}' creee/verifiee")
            except Exception as e:
                print(f"ERREUR creation table '{table_name}': {e}")
                return False
        
        return True
    
    def integrate_scraped_athletes(self, scraper_name):
        """Integre les derniers athletes scrapes"""
        
        # Mapping des noms de scrapers
        scraper_mapping = {
            'athletes2024': 'athletes_2024',
            'teamathletes': 'team_athletes',
            'wikipediateams': 'wikipedia_teams',
            'wikipedia': 'wikipedia',
            'olympics': 'olympics',
            'paris2024': 'paris2024'
        }
        
        # Utiliser le nom de fichier correct
        file_scraper_name = scraper_mapping.get(scraper_name, scraper_name)
        
        # Chercher le dernier fichier du scraper
        pattern = f"{file_scraper_name}_processed_*.csv"
        files = list(self.scraped_data_dir.glob(pattern))
        
        if not files:
            print(f"Aucun fichier traite trouve pour {scraper_name}")
            return False
        
        # Prendre le fichier le plus recent
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        
        try:
            # Charger les donnees
            df = pd.read_csv(latest_file, encoding='utf-8')
            print(f"Chargement de {len(df)} athletes depuis {latest_file.name}")
            
            # Nettoyer et standardiser
            df = self.clean_athletes_data(df)
            
            # Inserer en base
            success = self.db_conn.insert_dataframe(
                df, 
                'scraped_athletes_2024', 
                if_exists='append'  # Ajouter aux donnees existantes
            )
            
            if success:
                # Logger l'operation
                self.log_scraping_operation(
                    scraper_name, 
                    'SUCCESS', 
                    len(df), 
                    None, 
                    1.0
                )
                print(f"OK {len(df)} athletes integres en base")
                return True
            else:
                self.log_scraping_operation(
                    scraper_name, 
                    'FAILED', 
                    0, 
                    'Database insertion failed', 
                    1.0
                )
                return False
                
        except Exception as e:
            print(f"ERREUR integration athletes: {e}")
            self.log_scraping_operation(
                scraper_name, 
                'ERROR', 
                0, 
                str(e), 
                1.0
            )
            return False
    
    def clean_athletes_data(self, df):
        """Nettoie et standardise les donnees d'athletes"""
        
        # Colonnes requises
        required_columns = ['name', 'sport', 'country', 'age', 'birth_year', 
                          'profile_url', 'source', 'scraped_at', 'qualified_2024',
                          'details', 'type']
        
        # Ajouter les colonnes manquantes
        for col in required_columns:
            if col not in df.columns:
                if col in ['age', 'birth_year']:
                    df[col] = None
                elif col == 'qualified_2024':
                    df[col] = True  # Par defaut, on assume que scrapes = qualifies
                elif col in ['details', 'type']:
                    df[col] = ''
                else:
                    df[col] = ''
        
        # Nettoyer les noms
        df['name'] = df['name'].str.strip()
        df['name'] = df['name'].str.title()
        
        # Nettoyer les pays
        df['country'] = df['country'].str.strip()
        df['country'] = df['country'].str.title()
        
        # Standardiser les sports
        df['sport'] = df['sport'].str.strip()
        df['sport'] = df['sport'].str.title()
        
        # Nettoyer les URLs
        df['profile_url'] = df['profile_url'].fillna('')
        
        # Ajouter colonne medals_info si manquante
        if 'medals_info' not in df.columns:
            df['medals_info'] = ''
        
        # Supprimer les doublons
        df = df.drop_duplicates(subset=['name', 'source'], keep='first')
        
        # Filtrer les noms valides
        df = df[df['name'].str.len() > 2]
        df = df[~df['name'].str.startswith('SPORT_')]  # Supprimer les references sports
        
        return df
    
    def log_scraping_operation(self, scraper_name, status, records_count, error_message, execution_time):
        """Log une operation de scraping"""
        
        log_data = pd.DataFrame([{
            'scraper_name': scraper_name,
            'status': status,
            'records_count': records_count,
            'error_message': error_message,
            'execution_time': execution_time,
            'started_at': datetime.now(),
            'completed_at': datetime.now()
        }])
        
        try:
            self.db_conn.insert_dataframe(log_data, 'scraping_log', if_exists='append')
        except Exception as e:
            print(f"ERREUR logging: {e}")
    
    def get_scraped_athletes_stats(self):
        """Recupere les statistiques des athletes scrapes"""
        
        queries = {
            'total_athletes': "SELECT COUNT(*) as count FROM scraped_athletes_2024",
            'by_source': "SELECT source, COUNT(*) as count FROM scraped_athletes_2024 GROUP BY source",
            'by_country': "SELECT country, COUNT(*) as count FROM scraped_athletes_2024 WHERE country != '' GROUP BY country ORDER BY count DESC LIMIT 10",
            'qualified_count': "SELECT COUNT(*) as count FROM scraped_athletes_2024 WHERE qualified_2024 = true",
            'recent_scraping': "SELECT scraper_name, status, records_count, completed_at FROM scraping_log ORDER BY completed_at DESC LIMIT 5"
        }
        
        stats = {}
        for name, query in queries.items():
            try:
                result = self.db_conn.execute_query(query)
                stats[name] = result
            except Exception as e:
                print(f"ERREUR stats {name}: {e}")
                stats[name] = None
        
        return stats
    
    def merge_with_historical_data(self):
        """Fusionne avec les donnees historiques pour enrichir les predictions"""
        
        merge_query = '''
        SELECT 
            s.name as scraped_name,
            s.sport as scraped_sport,
            s.country as scraped_country,
            s.qualified_2024,
            h.full_name as historical_name,
            h.birth_year as historical_birth_year,
            h.medals_count as historical_medals,
            h.gold_medals,
            h.silver_medals,
            h.bronze_medals
        FROM scraped_athletes_2024 s
        LEFT JOIN olympic_athletes h ON (
            LOWER(s.name) = LOWER(h.full_name) 
            OR LOWER(s.name) LIKE LOWER('%' || h.full_name || '%')
            OR LOWER(h.full_name) LIKE LOWER('%' || s.name || '%')
        )
        WHERE s.qualified_2024 = true
        ORDER BY s.name
        '''
        
        try:
            result = self.db_conn.execute_query(merge_query)
            print(f"Fusion realisee: {len(result)} correspondances trouvees")
            return result
        except Exception as e:
            print(f"ERREUR fusion donnees: {e}")
            return None
    
    def run_full_integration(self, scraper_names=['test']):
        """Execute l'integration complete"""
        
        print("=== INTEGRATION DONNEES SCRAPEES ===")
        print()
        
        # 1. Creer les tables
        print("1. Creation des tables...")
        if not self.create_scraped_tables():
            return False
        
        # 2. Integrer les donnees de chaque scraper
        print("2. Integration des donnees...")
        for scraper_name in scraper_names:
            print(f"   - Integration {scraper_name}...")
            self.integrate_scraped_athletes(scraper_name)
        
        # 3. Afficher les statistiques
        print("3. Statistiques...")
        stats = self.get_scraped_athletes_stats()
        
        if stats['total_athletes'] is not None:
            total = stats['total_athletes'].iloc[0]['count']
            print(f"   Total athletes scrapes: {total}")
        
        if stats['qualified_count'] is not None:
            qualified = stats['qualified_count'].iloc[0]['count']
            print(f"   Athletes qualifies 2024: {qualified}")
        
        if stats['by_source'] is not None and not stats['by_source'].empty:
            print("   Par source:")
            for _, row in stats['by_source'].iterrows():
                print(f"     - {row['source']}: {row['count']}")
        
        # 4. Fusion avec donnees historiques
        print("4. Fusion avec donnees historiques...")
        merged_data = self.merge_with_historical_data()
        if merged_data is not None:
            matches = len(merged_data[merged_data['historical_name'].notna()])
            print(f"   {matches} athletes avec historique trouve")
        
        print()
        print("=== INTEGRATION TERMINEE ===")
        return True

if __name__ == "__main__":
    integrator = ScrapingDBIntegrator()
    
    # Tester la connexion
    if integrator.db_conn.test_connection():
        # Lancer l'integration avec les donnees de test
        integrator.run_full_integration(['test'])
    else:
        print("ERREUR: Impossible de se connecter a la base de donnees")