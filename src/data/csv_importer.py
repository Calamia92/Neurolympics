"""
Importateur CSV pour les donnees athletes Paris 2024
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
from sqlalchemy import text
from src.database.connection import get_db_connection
import json
from datetime import datetime
import ast

class Paris2024CSVImporter:
    """Importateur CSV vers base Paris 2024"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def parse_list_field(self, field_value):
        """Parser champ liste (disciplines/events)"""
        if pd.isna(field_value) or not field_value:
            return []
        
        if isinstance(field_value, str):
            if field_value.startswith('['):
                try:
                    return ast.literal_eval(field_value)
                except:
                    return []
            else:
                return [field_value]
        
        return []
    
    def calculate_age(self, birth_date):
        """Calculer age depuis date naissance"""
        if pd.isna(birth_date):
            return None
        
        try:
            if isinstance(birth_date, str):
                birth_year = int(birth_date.split('-')[0])
            else:
                birth_year = birth_date.year
            
            return 2024 - birth_year
        except:
            return None
    
    def clean_athlete_data(self, row):
        """Nettoyer donnees d'un athlete"""
        
        # Donnees de base
        clean_data = {
            'name': row['name'].strip() if pd.notna(row['name']) else None,
            'country': row['country'].strip() if pd.notna(row['country']) else None,
            'country_code': row['country_code'].strip() if pd.notna(row['country_code']) else None,
            'gender': row['gender'] if pd.notna(row['gender']) else None,
        }
        
        # Sports et disciplines
        disciplines = self.parse_list_field(row['disciplines'])
        events = self.parse_list_field(row['events'])
        
        if disciplines:
            clean_data['sport'] = disciplines[0]  # Premier sport
            clean_data['discipline'] = ', '.join(disciplines)
        else:
            clean_data['sport'] = 'Unknown'
            clean_data['discipline'] = None
        
        clean_data['events'] = events
        
        # Age et date naissance
        clean_data['date_of_birth'] = row['birth_date'] if pd.notna(row['birth_date']) else None
        clean_data['age'] = self.calculate_age(row['birth_date'])
        
        # Donnees physiques
        height = row['height'] if pd.notna(row['height']) and row['height'] > 0 else None
        weight = row['weight'] if pd.notna(row['weight']) and row['weight'] > 0 else None
        
        clean_data['height'] = int(height) if height else None
        clean_data['weight'] = int(weight) if weight else None
        
        # Informations personnelles
        bio_parts = []
        
        if pd.notna(row['birth_place']):
            bio_parts.append(f"Born in {row['birth_place']}")
        
        if pd.notna(row['nickname']):
            bio_parts.append(f"Nickname: {row['nickname']}")
        
        if pd.notna(row['occupation']):
            bio_parts.append(f"Occupation: {row['occupation']}")
        
        if pd.notna(row['education']):
            bio_parts.append(f"Education: {row['education'][:200]}")  # Limiter taille
        
        clean_data['bio_short'] = '. '.join(bio_parts) if bio_parts else None
        
        # Donnees enrichies JSONB
        personal_data = {}
        
        for field in ['nickname', 'hobbies', 'coach', 'hero', 'philosophy', 'family']:
            if pd.notna(row[field]) and row[field].strip():
                personal_data[field] = row[field].strip()
        
        clean_data['personal_best'] = json.dumps(personal_data) if personal_data else None
        
        # Metadonnees
        clean_data['data_source'] = 'paris2024_official_csv'
        clean_data['scraped_at'] = datetime.now()
        
        return clean_data
    
    def import_athletes(self, csv_path, batch_size=100):
        """Importer athletes par lots"""
        
        print(f"Import CSV: {csv_path}")
        
        # Charger CSV
        df = pd.read_csv(csv_path)
        print(f"Total athletes dans CSV: {len(df)}")
        
        # Filtrer seulement athletes actifs
        if 'current' in df.columns:
            df = df[df['current'] == True]
            print(f"Athletes actifs (current=True): {len(df)}")
        
        # Traiter par lots
        total_inserted = 0
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(df))
            
            batch_df = df.iloc[start_idx:end_idx]
            
            print(f"Lot {batch_num + 1}/{total_batches}: athletes {start_idx+1}-{end_idx}")
            
            batch_inserted = self.insert_batch(batch_df)
            total_inserted += batch_inserted
            
            if batch_num % 10 == 0:  # Progres tous les 10 lots
                print(f"  Progres: {total_inserted} athletes inseres")
        
        print(f"\\nImport termine: {total_inserted}/{len(df)} athletes inseres")
        return total_inserted
    
    def insert_batch(self, batch_df):
        """Inserer un lot d'athletes"""
        
        inserted_count = 0
        
        for _, row in batch_df.iterrows():
            try:
                clean_data = self.clean_athlete_data(row)
                
                # Verifier donnees minimales
                if not clean_data['name'] or not clean_data['country']:
                    continue
                
                # Query UPSERT
                query = """
                INSERT INTO paris2024_athletes (
                    name, country, country_code, sport, discipline, events, 
                    gender, age, date_of_birth, height, weight, bio_short,
                    personal_best, data_source, scraped_at
                ) VALUES (
                    :name, :country, :country_code, :sport, :discipline, :events,
                    :gender, :age, :date_of_birth, :height, :weight, :bio_short,
                    CAST(:personal_best AS jsonb), :data_source, :scraped_at
                )
                ON CONFLICT (name, country, sport) 
                DO UPDATE SET
                    country_code = EXCLUDED.country_code,
                    discipline = EXCLUDED.discipline,
                    events = EXCLUDED.events,
                    gender = EXCLUDED.gender,
                    age = EXCLUDED.age,
                    date_of_birth = EXCLUDED.date_of_birth,
                    height = EXCLUDED.height,
                    weight = EXCLUDED.weight,
                    bio_short = EXCLUDED.bio_short,
                    personal_best = EXCLUDED.personal_best,
                    last_updated = CURRENT_TIMESTAMP
                """
                
                with self.db.engine.connect() as conn:
                    conn.execute(text(query), clean_data)
                    conn.commit()
                
                inserted_count += 1
                
            except Exception as e:
                print(f"Erreur athlete {row.get('name', 'Unknown')}: {e}")
                continue
        
        return inserted_count
    
    def import_countries(self, csv_path):
        """Importer/mettre a jour pays"""
        
        df = pd.read_csv(csv_path)
        
        if 'current' in df.columns:
            df = df[df['current'] == True]
        
        # Grouper par pays
        countries = df.groupby(['country', 'country_code']).size().reset_index(name='total_athletes')
        
        print(f"\\nImport pays: {len(countries)} pays")
        
        inserted_count = 0
        
        for _, country_row in countries.iterrows():
            try:
                query = """
                INSERT INTO paris2024_countries (
                    country_name, country_code, total_athletes
                ) VALUES (:country_name, :country_code, :total_athletes)
                ON CONFLICT (country_code)
                DO UPDATE SET
                    country_name = EXCLUDED.country_name,
                    total_athletes = EXCLUDED.total_athletes
                """
                
                with self.db.engine.connect() as conn:
                    conn.execute(text(query), {
                        'country_name': country_row['country'],
                        'country_code': country_row['country_code'],
                        'total_athletes': int(country_row['total_athletes'])
                    })
                    conn.commit()
                
                inserted_count += 1
                
            except Exception as e:
                print(f"Erreur pays {country_row['country']}: {e}")
                continue
        
        print(f"Pays inseres/mis a jour: {inserted_count}")
        return inserted_count
    
    def get_import_stats(self):
        """Statistiques post-import"""
        
        stats = {}
        
        # Total athletes
        result = self.db.execute_query("SELECT COUNT(*) as total FROM paris2024_athletes")
        if result is not None and not result.empty:
            stats['total_athletes'] = result.iloc[0]['total']
        
        # Par pays (top 10)
        result = self.db.execute_query("""
            SELECT country, COUNT(*) as count 
            FROM paris2024_athletes 
            GROUP BY country 
            ORDER BY count DESC 
            LIMIT 10
        """)
        if result is not None and not result.empty:
            stats['top_countries'] = result.to_dict('records')
        
        # Par sport
        result = self.db.execute_query("""
            SELECT sport, COUNT(*) as count 
            FROM paris2024_athletes 
            GROUP BY sport 
            ORDER BY count DESC 
            LIMIT 10
        """)
        if result is not None and not result.empty:
            stats['top_sports'] = result.to_dict('records')
        
        # Qualite donnees
        result = self.db.execute_query("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN age IS NOT NULL THEN 1 END) as with_age,
                COUNT(CASE WHEN height IS NOT NULL THEN 1 END) as with_height,
                COUNT(CASE WHEN weight IS NOT NULL THEN 1 END) as with_weight,
                COUNT(CASE WHEN bio_short IS NOT NULL THEN 1 END) as with_bio,
                COUNT(CASE WHEN personal_best IS NOT NULL THEN 1 END) as with_personal,
                COUNT(CASE WHEN events IS NOT NULL AND array_length(events, 1) > 0 THEN 1 END) as with_events
            FROM paris2024_athletes
        """)
        if result is not None and not result.empty:
            stats['data_quality'] = result.iloc[0].to_dict()
        
        return stats

if __name__ == "__main__":
    importer = Paris2024CSVImporter()
    
    csv_file = "data/exports/athletes.csv"
    
    print("=== IMPORT CSV ATHLETES PARIS 2024 ===")
    
    # 1. Import athletes
    athletes_imported = importer.import_athletes(csv_file, batch_size=200)
    
    # 2. Import pays
    countries_imported = importer.import_countries(csv_file)
    
    # 3. Statistiques finales
    print("\\n=== STATISTIQUES FINALES ===")
    stats = importer.get_import_stats()
    
    print(f"Total athletes: {stats.get('total_athletes', 0)}")
    
    if stats.get('top_countries'):
        print("\\nTop 10 pays:")
        for country in stats['top_countries']:
            print(f"  {country['country']}: {country['count']} athletes")
    
    if stats.get('top_sports'):
        print("\\nTop 10 sports:")
        for sport in stats['top_sports']:
            print(f"  {sport['sport']}: {sport['count']} athletes")
    
    if stats.get('data_quality'):
        quality = stats['data_quality']
        total = quality['total']
        print(f"\\nQualite donnees:")
        print(f"  Avec age: {quality['with_age']}/{total} ({quality['with_age']/total*100:.1f}%)")
        print(f"  Avec taille: {quality['with_height']}/{total} ({quality['with_height']/total*100:.1f}%)")
        print(f"  Avec poids: {quality['with_weight']}/{total} ({quality['with_weight']/total*100:.1f}%)")
        print(f"  Avec bio: {quality['with_bio']}/{total} ({quality['with_bio']/total*100:.1f}%)")
        print(f"  Avec donnees perso: {quality['with_personal']}/{total} ({quality['with_personal']/total*100:.1f}%)")
        print(f"  Avec epreuves: {quality['with_events']}/{total} ({quality['with_events']/total*100:.1f}%)")
    
    print(f"\\nImport termine avec succes!")