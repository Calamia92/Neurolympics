"""
Scraper pour le site officiel Paris 2024
Recupere les listes d'athletes qualifies et les informations sur les epreuves
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

class Paris2024Scraper(BaseScraper):
    """Scraper pour paris2024.org"""
    
    def __init__(self):
        super().__init__("paris2024")
        self.base_url = "https://www.paris2024.org"
        self.rate_limit = 2.0  # Plus conservateur pour le site officiel
    
    def scrape(self):
        """Scrape les principales pages de Paris 2024"""
        
        scraped_data = {
            'sports': self.scrape_sports(),
            'athletes': self.scrape_athletes_pages(),
            'schedule': self.scrape_schedule(),
            'venues': self.scrape_venues()
        }
        
        return scraped_data
    
    def scrape_sports(self):
        """Recupere la liste des sports et disciplines"""
        sports_url = f"{self.base_url}/fr/sports"
        
        content = self.fetch_url(sports_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        sports_data = []
        
        # Chercher les liens vers les sports
        sport_links = soup.find_all('a', href=re.compile(r'/fr/sports/'))
        
        for link in sport_links:
            sport_name = link.get_text(strip=True)
            sport_url = link.get('href')
            
            if sport_name and sport_url and sport_name not in [s['name'] for s in sports_data]:
                sports_data.append({
                    'name': sport_name,
                    'url': sport_url if sport_url.startswith('http') else self.base_url + sport_url,
                    'scraped_at': datetime.now().isoformat()
                })
        
        self.logger.info(f"Found {len(sports_data)} sports")
        return sports_data
    
    def scrape_athletes_pages(self):
        """Recupere les pages d'athletes"""
        # Pages potentielles d'athletes
        athlete_urls = [
            f"{self.base_url}/fr/athletes",
            f"{self.base_url}/fr/equipe-france"
        ]
        
        athletes_data = []
        
        for url in athlete_urls:
            content = self.fetch_url(url)
            if content:
                athletes_data.extend(self.parse_athletes_page(content, url))
        
        self.logger.info(f"Found {len(athletes_data)} athletes")
        return athletes_data
    
    def parse_athletes_page(self, content, source_url):
        """Parse une page d'athletes"""
        soup = BeautifulSoup(content, 'html.parser')
        athletes = []
        
        # Chercher differents patterns d'athletes
        patterns = [
            {'class': 'athlete-card'},
            {'class': 'athlete-item'},
            {'class': 'player-card'},
            {'data-athlete': True},
        ]
        
        for pattern in patterns:
            athlete_elements = soup.find_all(attrs=pattern)
            
            for element in athlete_elements:
                athlete_info = self.extract_athlete_info(element)
                if athlete_info:
                    athlete_info['source_url'] = source_url
                    athlete_info['scraped_at'] = datetime.now().isoformat()
                    athletes.append(athlete_info)
        
        # Si pas trouve avec les patterns, chercher les liens vers des profils
        if not athletes:
            profile_links = soup.find_all('a', href=re.compile(r'/(athlete|profil|player)'))
            for link in profile_links[:50]:  # Limiter pour eviter le spam
                athlete_name = link.get_text(strip=True)
                athlete_url = link.get('href')
                
                if athlete_name and len(athlete_name.split()) >= 2:  # Au moins prenom nom
                    athletes.append({
                        'name': athlete_name,
                        'profile_url': athlete_url if athlete_url.startswith('http') else self.base_url + athlete_url,
                        'source_url': source_url,
                        'scraped_at': datetime.now().isoformat()
                    })
        
        return athletes
    
    def extract_athlete_info(self, element):
        """Extrait les infos d'un element athlete"""
        info = {}
        
        # Nom
        name_selectors = ['h1', 'h2', 'h3', '.name', '.athlete-name', '.player-name']
        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                info['name'] = name_elem.get_text(strip=True)
                break
        
        # Sport/Discipline
        sport_selectors = ['.sport', '.discipline', '.category']
        for selector in sport_selectors:
            sport_elem = element.select_one(selector)
            if sport_elem:
                info['sport'] = sport_elem.get_text(strip=True)
                break
        
        # Pays
        country_selectors = ['.country', '.nationality', '.flag']
        for selector in country_selectors:
            country_elem = element.select_one(selector)
            if country_elem:
                info['country'] = country_elem.get_text(strip=True)
                break
        
        # URL du profil
        profile_link = element.find('a')
        if profile_link:
            href = profile_link.get('href')
            if href:
                info['profile_url'] = href if href.startswith('http') else self.base_url + href
        
        # Age/Date de naissance
        age_text = element.get_text()
        age_match = re.search(r'(\d{1,2})\s*ans?|born\s*(\d{4})|ne.*(\d{4})', age_text, re.IGNORECASE)
        if age_match:
            if age_match.group(1):  # Age
                info['age'] = int(age_match.group(1))
            elif age_match.group(2) or age_match.group(3):  # Annee de naissance
                birth_year = int(age_match.group(2) or age_match.group(3))
                info['birth_year'] = birth_year
                info['age'] = 2024 - birth_year
        
        return info if info else None
    
    def scrape_schedule(self):
        """Recupere le calendrier des epreuves"""
        schedule_url = f"{self.base_url}/fr/calendrier"
        
        content = self.fetch_url(schedule_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        events = []
        
        # Chercher les evenements
        event_selectors = ['.event', '.competition', '.match', '.epreuve']
        
        for selector in event_selectors:
            event_elements = soup.select(selector)
            for event in event_elements:
                event_info = self.extract_event_info(event)
                if event_info:
                    event_info['scraped_at'] = datetime.now().isoformat()
                    events.append(event_info)
        
        self.logger.info(f"Found {len(events)} events")
        return events
    
    def extract_event_info(self, element):
        """Extrait les infos d'un evenement"""
        info = {}
        
        # Titre de l'evenement
        title_elem = element.select_one('h1, h2, h3, .title, .event-title')
        if title_elem:
            info['title'] = title_elem.get_text(strip=True)
        
        # Date
        date_elem = element.select_one('.date, .datetime, time')
        if date_elem:
            info['date'] = date_elem.get_text(strip=True)
        
        # Sport
        sport_elem = element.select_one('.sport, .discipline')
        if sport_elem:
            info['sport'] = sport_elem.get_text(strip=True)
        
        # Lieu
        venue_elem = element.select_one('.venue, .location, .lieu')
        if venue_elem:
            info['venue'] = venue_elem.get_text(strip=True)
        
        return info if len(info) >= 2 else None
    
    def scrape_venues(self):
        """Recupere les lieux de competition"""
        venues_url = f"{self.base_url}/fr/lieux"
        
        content = self.fetch_url(venues_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        venues = []
        
        venue_links = soup.find_all('a', href=re.compile(r'/lieux|/venue'))
        
        for link in venue_links:
            venue_name = link.get_text(strip=True)
            venue_url = link.get('href')
            
            if venue_name and venue_url:
                venues.append({
                    'name': venue_name,
                    'url': venue_url if venue_url.startswith('http') else self.base_url + venue_url,
                    'scraped_at': datetime.now().isoformat()
                })
        
        self.logger.info(f"Found {len(venues)} venues")
        return venues
    
    def parse_data(self, raw_data):
        """Transforme les donnees brutes en DataFrames structures"""
        
        # Creer un DataFrame principal avec tous les athletes
        athletes_list = []
        
        if 'athletes' in raw_data and raw_data['athletes']:
            for athlete in raw_data['athletes']:
                if isinstance(athlete, dict) and athlete.get('name'):
                    athletes_list.append({
                        'name': athlete.get('name', ''),
                        'sport': athlete.get('sport', ''),
                        'country': athlete.get('country', 'France'),  # Par defaut France sur paris2024.org
                        'age': athlete.get('age'),
                        'birth_year': athlete.get('birth_year'),
                        'profile_url': athlete.get('profile_url', ''),
                        'source': 'paris2024.org',
                        'scraped_at': athlete.get('scraped_at', datetime.now().isoformat()),
                        'qualified_2024': True  # Tous les athletes sur paris2024 sont qualifies
                    })
        
        # Ajouter les sports comme reference
        if 'sports' in raw_data and raw_data['sports']:
            for sport in raw_data['sports']:
                if isinstance(sport, dict) and sport.get('name'):
                    # Ajouter un athlete "placeholder" pour chaque sport pour garder la trace
                    athletes_list.append({
                        'name': f"SPORT_{sport['name']}",
                        'sport': sport['name'],
                        'country': 'REFERENCE',
                        'age': None,
                        'birth_year': None,
                        'profile_url': sport.get('url', ''),
                        'source': 'paris2024.org_sports',
                        'scraped_at': sport.get('scraped_at', datetime.now().isoformat()),
                        'qualified_2024': False  # Ce sont des references, pas des athletes
                    })
        
        if not athletes_list:
            self.logger.warning("No athletes data found to process")
            return pd.DataFrame()
        
        df = pd.DataFrame(athletes_list)
        
        # Nettoyage des donnees
        df = df.drop_duplicates(subset=['name', 'sport'], keep='first')
        df = df[df['name'].str.len() > 0]  # Supprimer les noms vides
        
        self.logger.info(f"Processed {len(df)} athlete records")
        return df

if __name__ == "__main__":
    # Test du scraper
    scraper = Paris2024Scraper()
    data = scraper.run()
    
    if data is not None:
        print(f"Scraping successful: {len(data)} records")
        print("\nFirst 5 records:")
        print(data.head())
        
        print(f"\nColumns: {list(data.columns)}")
        print(f"Countries: {data['country'].value_counts().head()}")
        print(f"Sports: {data['sport'].value_counts().head()}")
    else:
        print("Scraping failed")