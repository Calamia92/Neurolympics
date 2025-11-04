"""
Scraper specialise pour recuperer les athletes qualifies Paris 2024
Sources: Wikipedia specialisees, World Athletics, sites olympiques
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.scraping.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime

class Athletes2024Scraper(BaseScraper):
    """Scraper pour athletes qualifies Paris 2024"""
    
    def __init__(self):
        super().__init__("athletes_2024")
        self.base_url = "https://en.wikipedia.org"
        self.rate_limit = 1.0
    
    def scrape(self):
        """Scrape plusieurs sources pour athletes 2024"""
        
        scraped_data = {
            'athletics_qualified': self.scrape_athletics_qualified(),
            'swimming_qualified': self.scrape_swimming_qualified(),
            'french_team': self.scrape_french_team(),
            'world_athletics': self.scrape_world_athletics_sample()
        }
        
        return scraped_data
    
    def scrape_athletics_qualified(self):
        """Scrape la page d'athletisme pour athletes qualifies"""
        url = f"{self.base_url}/wiki/Athletics_at_the_2024_Summer_Olympics"
        
        content = self.fetch_url(url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        qualified_athletes = []
        
        # Chercher les tableaux avec des qualifications
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        for table in tables:
            # Chercher les headers pour identifier les tableaux d'athletes
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            
            if any(keyword in ' '.join(headers) for keyword in ['athlete', 'competitor', 'name', 'country']):
                rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows[:50]:  # Limiter pour eviter surcharge
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        athlete_info = self.extract_athlete_from_row(cells, 'athletics')
                        if athlete_info:
                            qualified_athletes.append(athlete_info)
        
        return qualified_athletes[:100]  # Max 100
    
    def scrape_swimming_qualified(self):
        """Scrape la page de natation pour athletes qualifies"""
        url = f"{self.base_url}/wiki/Swimming_at_the_2024_Summer_Olympics"
        
        content = self.fetch_url(url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        qualified_athletes = []
        
        # Chercher specifiquement les sections de qualification
        sections = soup.find_all(['h3', 'h4'], string=re.compile(r'qualified|qualification', re.IGNORECASE))
        
        for section in sections:
            # Chercher le tableau suivant
            next_table = section.find_next('table', {'class': 'wikitable'})
            if next_table:
                rows = next_table.find_all('tr')[1:]
                
                for row in rows[:30]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        athlete_info = self.extract_athlete_from_row(cells, 'swimming')
                        if athlete_info:
                            qualified_athletes.append(athlete_info)
        
        return qualified_athletes[:50]
    
    def scrape_french_team(self):
        """Scrape pour l'equipe de France specifiquement"""
        # Utiliser Wikipedia FR pour plus de details sur l'equipe francaise
        url = "https://fr.wikipedia.org/wiki/France_aux_Jeux_olympiques_d%27été_de_2024"
        
        content = self.fetch_url(url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        french_athletes = []
        
        # Chercher les tableaux d'athletes francais
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    athlete_info = self.extract_athlete_from_row(cells, 'france_team')
                    if athlete_info:
                        athlete_info['country'] = 'France'  # Force le pays
                        french_athletes.append(athlete_info)
        
        return french_athletes[:100]
    
    def scrape_world_athletics_sample(self):
        """Sample du site World Athletics (structure complexe)"""
        url = "https://worldathletics.org/world-rankings"
        
        content = self.fetch_url(url, use_cache=True, cache_hours=6)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        athletes_sample = []
        
        # Chercher les noms d'athletes dans les rankings
        athlete_links = soup.find_all('a', href=re.compile(r'athletes|profile'))
        
        for link in athlete_links[:30]:  # Sample limite
            text = link.get_text(strip=True)
            if self.is_potential_athlete_name(text):
                athletes_sample.append({
                    'name': text,
                    'source_url': link.get('href', ''),
                    'sport': 'athletics',
                    'ranking_source': 'world_athletics'
                })
        
        return athletes_sample
    
    def extract_athlete_from_row(self, cells, sport_context):
        """Extrait info athlete depuis une ligne de tableau"""
        athlete_name = ''
        country = ''
        additional_info = []
        
        for i, cell in enumerate(cells[:4]):  # Max 4 colonnes
            text = cell.get_text(strip=True)
            
            # Nettoyer le texte
            text = re.sub(r'\[.*?\]', '', text).strip()
            
            if i == 0 and self.is_potential_athlete_name(text):
                athlete_name = text
            elif i == 1:
                if self.is_potential_country(text):
                    country = text
                elif not athlete_name and self.is_potential_athlete_name(text):
                    athlete_name = text
            else:
                if text and len(text) < 100:
                    additional_info.append(text)
        
        if athlete_name and len(athlete_name) > 2:
            return {
                'name': athlete_name,
                'country': country,
                'sport': sport_context,
                'additional_info': ' | '.join(additional_info),
                'extraction_context': 'table_row'
            }
        
        return None
    
    def is_potential_country(self, text):
        """Determine si le texte ressemble a un nom de pays"""
        if not text or len(text) < 2 or len(text) > 30:
            return False
        
        # Codes pays courants
        country_codes = ['FRA', 'USA', 'GBR', 'GER', 'ITA', 'ESP', 'CAN', 'AUS', 'JPN', 'CHN']
        if text.upper() in country_codes:
            return True
        
        # Noms de pays courants
        countries = ['France', 'United States', 'Germany', 'Italy', 'Spain', 'Canada', 
                    'Australia', 'Japan', 'China', 'Britain', 'Netherlands']
        if any(country.lower() in text.lower() for country in countries):
            return True
        
        return False
    
    def is_potential_athlete_name(self, text):
        """Determine si un texte ressemble a un nom d'athlete (improved)"""
        if not text or len(text) < 3 or len(text) > 40:
            return False
        
        words = text.split()
        if len(words) < 2 or len(words) > 3:
            return False
        
        # Doit etre principalement des lettres
        alpha_ratio = sum(c.isalpha() or c.isspace() or c in '-.\'' for c in text) / len(text)
        if alpha_ratio < 0.8:
            return False
        
        # Doit commencer par une majuscule
        if not text[0].isupper():
            return False
        
        # Eviter les faux positifs courants
        false_positives = {'Main Page', 'Current Events', 'Random Article', 'About Wikipedia', 
                          'Contact Us', 'Event', 'Date', 'Time', 'Result', 'Record', 'Rank'}
        if any(fp.lower() in text.lower() for fp in false_positives):
            return False
        
        # Eviter les mots communs
        common_words = {'the', 'and', 'or', 'at', 'in', 'on', 'for', 'with', 'by', 'from', 'to', 'of', 'as'}
        if any(word.lower() in common_words for word in words):
            return False
        
        return True
    
    def parse_data(self, raw_data):
        """Transforme les donnees brutes en DataFrame structure"""
        
        all_athletes = []
        
        # Traiter chaque source
        for source_name, athletes_list in raw_data.items():
            if athletes_list:
                for athlete in athletes_list:
                    if isinstance(athlete, dict) and athlete.get('name'):
                        record = {
                            'name': athlete['name'],
                            'sport': athlete.get('sport', ''),
                            'country': athlete.get('country', ''),
                            'age': None,
                            'birth_year': None,
                            'profile_url': athlete.get('source_url', ''),
                            'details': athlete.get('additional_info', ''),
                            'source': f'athletes_2024_{source_name}',
                            'scraped_at': datetime.now().isoformat(),
                            'qualified_2024': True,  # Ces athletes sont consideres qualifies
                            'type': 'qualified_athlete_2024'
                        }
                        all_athletes.append(record)
        
        if not all_athletes:
            self.logger.warning("No qualified athletes found")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_athletes)
        
        # Nettoyage et deduplication
        df = df.drop_duplicates(subset=['name', 'sport'], keep='first')
        df = df[df['name'].str.len() > 2]
        
        # Filtrer les faux positifs restants
        df = df[~df['name'].str.contains('Event|Date|Time|Result', case=False, na=False)]
        
        self.logger.info(f"Processed {len(df)} qualified athletes for 2024")
        return df

if __name__ == "__main__":
    # Test du scraper athletes 2024
    scraper = Athletes2024Scraper()
    data = scraper.run()
    
    if data is not None and not data.empty:
        print(f"Scraping Athletes 2024 reussi: {len(data)} athletes qualifies")
        print()
        print("Repartition par sport:")
        print(data['sport'].value_counts())
        print()
        print("Repartition par pays:")
        print(data['country'].value_counts().head(10))
        print()
        print("Exemples d'athletes qualifies:")
        for _, athlete in data.head(10).iterrows():
            print(f"  - {athlete['name']} ({athlete['sport']}, {athlete['country']})")
    else:
        print("Echec du scraping Athletes 2024")