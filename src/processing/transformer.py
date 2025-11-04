"""
Module de transformation et normalisation des datasets olympiques
Transforme les 4 formats (JSON, XML, XLSX, HTML) vers un schéma uniforme
"""

import pandas as pd
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
import re

class OlympicDataTransformer:
    def __init__(self):
        self.datasets_path = "data/raw/"
        
    def transform_athletes_json(self, filepath):
        """Transforme le fichier JSON des athlètes"""
        print("Transformation des donnees athletes (JSON)...")
        
        # Lecture par chunks pour gérer le gros fichier
        athletes_data = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for athlete in data:
                # Nettoyage des médailles
                medals = self._clean_medals_text(athlete.get('athlete_medals', ''))
                
                athletes_data.append({
                    'athlete_id': self._extract_id_from_url(athlete.get('athlete_url', '')),
                    'athlete_url': athlete.get('athlete_url', ''),
                    'full_name': athlete.get('athlete_full_name', ''),
                    'birth_year': athlete.get('athlete_year_birth'),
                    'games_participations': athlete.get('games_participations', 0),
                    'first_game': athlete.get('first_game', ''),
                    'medals_count': self._count_medals(medals),
                    'gold_medals': medals.get('gold', 0),
                    'silver_medals': medals.get('silver', 0),
                    'bronze_medals': medals.get('bronze', 0),
                    'bio': athlete.get('bio', ''),
                    'data_source': 'json'
                })
                
        except Exception as e:
            print(f"Erreur lors de la transformation JSON: {e}")
            return pd.DataFrame()
            
        return pd.DataFrame(athletes_data)
    
    def transform_hosts_xml(self, filepath):
        """Transforme le fichier XML des villes hôtes"""
        print("Transformation des donnees hotes (XML)...")
        
        hosts_data = []
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            for row in root.findall('row'):
                hosts_data.append({
                    'game_id': row.find('index').text if row.find('index') is not None else None,
                    'game_slug': row.find('game_slug').text if row.find('game_slug') is not None else '',
                    'game_name': row.find('game_name').text if row.find('game_name') is not None else '',
                    'game_year': int(row.find('game_year').text) if row.find('game_year') is not None else None,
                    'game_season': row.find('game_season').text if row.find('game_season') is not None else '',
                    'host_location': row.find('game_location').text if row.find('game_location') is not None else '',
                    'start_date': self._parse_date(row.find('game_start_date').text if row.find('game_start_date') is not None else ''),
                    'end_date': self._parse_date(row.find('game_end_date').text if row.find('game_end_date') is not None else ''),
                    'data_source': 'xml'
                })
                
        except Exception as e:
            print(f"Erreur lors de la transformation XML: {e}")
            return pd.DataFrame()
            
        return pd.DataFrame(hosts_data)
    
    def transform_medals_xlsx(self, filepath):
        """Transforme le fichier Excel des médailles"""
        print("Transformation des donnees medailles (XLSX)...")
        
        try:
            df = pd.read_excel(filepath)
            
            # Nettoyage et normalisation
            medals_data = []
            for _, row in df.iterrows():
                medals_data.append({
                    'medal_id': len(medals_data) + 1,
                    'discipline': row.get('discipline_title', ''),
                    'event_title': row.get('event_title', ''),
                    'game_slug': row.get('slug_game', ''),
                    'event_gender': row.get('event_gender', ''),
                    'medal_type': row.get('medal_type', ''),
                    'participant_type': row.get('participant_type', ''),
                    'athlete_url': row.get('athlete_url', ''),
                    'athlete_name': row.get('athlete_full_name', ''),
                    'country_name': row.get('country_name', ''),
                    'country_code': row.get('country_code', ''),
                    'country_code_3': row.get('country_3_letter_code', ''),
                    'data_source': 'xlsx'
                })
                
        except Exception as e:
            print(f"Erreur lors de la transformation XLSX: {e}")
            return pd.DataFrame()
            
        return pd.DataFrame(medals_data)
    
    def transform_results_html(self, filepath):
        """Transforme le fichier HTML des résultats"""
        print("Transformation des donnees resultats (HTML)...")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            table = soup.find('table')
            
            if not table:
                print("Aucune table trouvée dans le fichier HTML")
                return pd.DataFrame()
            
            # Extraction des données de la table
            df = pd.read_html(str(table))[0]
            
            # Normalisation des colonnes
            results_data = []
            for _, row in df.iterrows():
                results_data.append({
                    'result_id': len(results_data) + 1,
                    'discipline': row.get('discipline_title', ''),
                    'event_title': row.get('event_title', ''),
                    'game_slug': row.get('slug_game', ''),
                    'participant_type': row.get('participant_type', ''),
                    'medal_type': row.get('medal_type', ''),
                    'athletes_info': str(row.get('athletes', '')),
                    'rank_position': row.get('rank_position', None),
                    'rank_equal': row.get('rank_equal', None),
                    'country_name': row.get('country_name', ''),
                    'country_code': row.get('country_code', ''),
                    'athlete_url': row.get('athlete_url', ''),
                    'athlete_name': row.get('athlete_full_name', ''),
                    'value_unit': row.get('value_unit', ''),
                    'value_type': row.get('value_type', ''),
                    'data_source': 'html'
                })
                
        except Exception as e:
            print(f"Erreur lors de la transformation HTML: {e}")
            return pd.DataFrame()
            
        return pd.DataFrame(results_data)
    
    def _extract_id_from_url(self, url):
        """Extrait un ID unique depuis l'URL de l'athlète"""
        if not url:
            return None
        # Extrait le dernier segment de l'URL
        return url.split('/')[-1] if '/' in url else url
    
    def _clean_medals_text(self, medals_text):
        """Nettoie et parse le texte des médailles"""
        if not medals_text or medals_text.strip() == '':
            return {'gold': 0, 'silver': 0, 'bronze': 0}
        
        medals = {'gold': 0, 'silver': 0, 'bronze': 0}
        
        # Recherche de patterns dans le texte
        gold_matches = re.findall(r'(\d+)\s*G', medals_text)
        silver_matches = re.findall(r'(\d+)\s*S', medals_text)
        bronze_matches = re.findall(r'(\d+)\s*B', medals_text)
        
        medals['gold'] = sum(int(x) for x in gold_matches)
        medals['silver'] = sum(int(x) for x in silver_matches)
        medals['bronze'] = sum(int(x) for x in bronze_matches)
        
        return medals
    
    def _count_medals(self, medals_dict):
        """Compte le nombre total de médailles"""
        return medals_dict['gold'] + medals_dict['silver'] + medals_dict['bronze']
    
    def _parse_date(self, date_string):
        """Parse une date ISO format"""
        if not date_string:
            return None
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00')).date()
        except:
            return None
    
    def create_unified_schema(self):
        """Crée un schéma unifié pour tous les datasets"""
        schema = {
            'athletes': {
                'athlete_id': 'varchar',
                'athlete_url': 'text',
                'full_name': 'varchar(255)',
                'birth_year': 'integer',
                'games_participations': 'integer',
                'first_game': 'varchar(100)',
                'medals_count': 'integer',
                'gold_medals': 'integer',
                'silver_medals': 'integer',
                'bronze_medals': 'integer',
                'bio': 'text',
                'data_source': 'varchar(10)'
            },
            'hosts': {
                'game_id': 'integer',
                'game_slug': 'varchar(100)',
                'game_name': 'varchar(100)',
                'game_year': 'integer',
                'game_season': 'varchar(20)',
                'host_location': 'varchar(100)',
                'start_date': 'date',
                'end_date': 'date',
                'data_source': 'varchar(10)'
            },
            'medals': {
                'medal_id': 'integer',
                'discipline': 'varchar(100)',
                'event_title': 'varchar(255)',
                'game_slug': 'varchar(100)',
                'event_gender': 'varchar(20)',
                'medal_type': 'varchar(20)',
                'participant_type': 'varchar(50)',
                'athlete_url': 'text',
                'athlete_name': 'varchar(255)',
                'country_name': 'varchar(100)',
                'country_code': 'varchar(10)',
                'country_code_3': 'varchar(10)',
                'data_source': 'varchar(10)'
            },
            'results': {
                'result_id': 'integer',
                'discipline': 'varchar(100)',
                'event_title': 'varchar(255)',
                'game_slug': 'varchar(100)',
                'participant_type': 'varchar(50)',
                'medal_type': 'varchar(20)',
                'athletes_info': 'text',
                'rank_position': 'integer',
                'rank_equal': 'boolean',
                'country_name': 'varchar(100)',
                'country_code': 'varchar(10)',
                'athlete_url': 'text',
                'athlete_name': 'varchar(255)',
                'value_unit': 'varchar(50)',
                'value_type': 'varchar(50)',
                'data_source': 'varchar(10)'
            }
        }
        return schema
    
    def transform_all_datasets(self):
        """Transforme tous les datasets"""
        print("=== Debut de la transformation des datasets ===")
        
        datasets = {}
        
        # Transform each dataset
        datasets['athletes'] = self.transform_athletes_json(f"{self.datasets_path}olympic_athletes.json")
        datasets['hosts'] = self.transform_hosts_xml(f"{self.datasets_path}olympic_hosts.xml")
        datasets['medals'] = self.transform_medals_xlsx(f"{self.datasets_path}olympic_medals.xlsx")
        datasets['results'] = self.transform_results_html(f"{self.datasets_path}olympic_results.html")
        
        # Affichage des statistiques
        for name, df in datasets.items():
            if not df.empty:
                print(f"OK {name}: {len(df)} lignes, {len(df.columns)} colonnes")
            else:
                print(f"ERREUR {name}: Echec de transformation")
        
        print("=== Transformation terminee ===")
        return datasets

if __name__ == "__main__":
    transformer = OlympicDataTransformer()
    datasets = transformer.transform_all_datasets()
    
    # Affichage du schéma unifié
    schema = transformer.create_unified_schema()
    print("\n=== Schéma unifié proposé ===")
    for table, columns in schema.items():
        print(f"\nTable: {table}")
        for col, dtype in columns.items():
            print(f"  - {col}: {dtype}")