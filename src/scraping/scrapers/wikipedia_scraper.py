"""
Scraper pour Wikipedia JO 2024 - Source fiable et accessible
Recupere les informations sur les sports, athletes et evenements
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

class WikipediaScraper(BaseScraper):
    """Scraper pour Wikipedia JO 2024"""
    
    def __init__(self):
        super().__init__("wikipedia")
        self.base_url = "https://en.wikipedia.org"
        self.rate_limit = 1.0  # Respectueux pour Wikipedia
    
    def scrape(self):
        """Scrape les pages Wikipedia liees aux JO 2024"""
        
        scraped_data = {
            'main_page': self.scrape_main_olympics_page(),
            'sports_list': self.scrape_sports_pages(),
            'venues': self.scrape_venues_page(),
            'athletes': self.scrape_athlete_mentions()
        }
        
        return scraped_data
    
    def scrape_main_olympics_page(self):
        """Scrape la page principale des JO 2024"""
        url = f"{self.base_url}/wiki/2024_Summer_Olympics"
        
        content = self.fetch_url(url)
        if not content:
            return {}
        
        soup = BeautifulSoup(content, 'html.parser')
        
        data = {
            'url': url,
            'title': soup.find('h1').get_text(strip=True) if soup.find('h1') else '',
            'sports': self.extract_sports_from_page(soup),
            'venues': self.extract_venues_from_page(soup),
            'dates': self.extract_dates_from_page(soup),
            'countries': self.extract_countries_from_page(soup)
        }
        
        return data
    
    def extract_sports_from_page(self, soup):
        """Extrait la liste des sports depuis la page principale"""
        sports = []
        
        # Chercher les tableaux avec des sports
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        for table in tables:
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            
            # Si le tableau contient des sports
            if any('sport' in header for header in headers):
                rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 1:
                        sport_name = cells[0].get_text(strip=True)
                        
                        # Nettoyer le nom du sport
                        sport_name = re.sub(r'\[.*?\]', '', sport_name).strip()
                        
                        if sport_name and len(sport_name) < 50:
                            sport_info = {
                                'name': sport_name,
                                'details': [cell.get_text(strip=True) for cell in cells[1:3]],
                                'source': 'wikipedia_main'
                            }
                            sports.append(sport_info)
        
        # Chercher aussi dans les listes
        sport_lists = soup.find_all('ul')
        for ul in sport_lists:
            items = ul.find_all('li')
            for item in items:
                text = item.get_text(strip=True)
                
                # Si ca ressemble a un sport
                if (len(text) < 30 and 
                    not text.startswith('http') and
                    any(sport_word in text.lower() for sport_word in ['ball', 'swim', 'athlet', 'gym', 'cycle', 'tennis', 'box', 'judo', 'weight'])):
                    
                    sports.append({
                        'name': text,
                        'details': [],
                        'source': 'wikipedia_list'
                    })
        
        return sports[:50]  # Limiter
    
    def extract_venues_from_page(self, soup):
        """Extrait les lieux de competition"""
        venues = []
        
        # Chercher les liens vers les venues
        venue_links = soup.find_all('a', href=re.compile(r'venue|stadium|arena|center|centre'))
        
        for link in venue_links[:20]:
            venue_name = link.get_text(strip=True)
            venue_url = link.get('href')
            
            if venue_name and len(venue_name) < 100:
                venues.append({
                    'name': venue_name,
                    'url': venue_url if venue_url.startswith('http') else self.base_url + venue_url,
                    'source': 'wikipedia_venues'
                })
        
        return venues
    
    def extract_dates_from_page(self, soup):
        """Extrait les dates importantes"""
        dates_info = []
        
        # Chercher les dates dans le texte
        text = soup.get_text()
        date_patterns = [
            r'(\d{1,2}\s+\w+\s+2024)',
            r'(July\s+\d{1,2}.*?2024)',
            r'(August\s+\d{1,2}.*?2024)'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:10]:
                dates_info.append({
                    'date_text': match,
                    'source': 'wikipedia_text'
                })
        
        return dates_info
    
    def extract_countries_from_page(self, soup):
        """Extrait les pays participants"""
        countries = []
        
        # Chercher les liens vers des pages de pays
        country_links = soup.find_all('a', href=re.compile(r'at_the_2024_Summer_Olympics'))
        
        for link in country_links[:50]:
            country_name = link.get_text(strip=True)
            country_url = link.get('href')
            
            if country_name and 'at the' not in country_name:
                countries.append({
                    'name': country_name,
                    'url': country_url if country_url.startswith('http') else self.base_url + country_url,
                    'source': 'wikipedia_countries'
                })
        
        return countries
    
    def scrape_sports_pages(self):
        """Scrape des pages specifiques de sports"""
        sports_urls = [
            f"{self.base_url}/wiki/Athletics_at_the_2024_Summer_Olympics",
            f"{self.base_url}/wiki/Swimming_at_the_2024_Summer_Olympics",
            f"{self.base_url}/wiki/Gymnastics_at_the_2024_Summer_Olympics"
        ]
        
        sports_data = []
        
        for url in sports_urls:
            content = self.fetch_url(url, cache_hours=12)
            if content:
                sport_info = self.parse_sport_page(content, url)
                if sport_info:
                    sports_data.append(sport_info)
        
        return sports_data
    
    def parse_sport_page(self, content, url):
        """Parse une page specifique de sport"""
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extraire le nom du sport depuis le titre
        title = soup.find('h1')
        sport_name = title.get_text(strip=True) if title else url.split('/')[-1]
        
        # Chercher les evenements/epreuves
        events = []
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        for table in tables[:3]:  # Limiter
            rows = table.find_all('tr')
            for row in rows[1:10]:  # Skip header, max 10
                cells = row.find_all(['td', 'th'])
                if cells:
                    event_text = cells[0].get_text(strip=True)
                    if event_text and len(event_text) < 100:
                        events.append(event_text)
        
        return {
            'sport_name': sport_name,
            'url': url,
            'events': events[:20],  # Max 20 events
            'source': 'wikipedia_sport_page'
        }
    
    def scrape_venues_page(self):
        """Scrape la page des lieux"""
        url = f"{self.base_url}/wiki/Venues_of_the_2024_Summer_Olympics"
        
        content = self.fetch_url(url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        venues = []
        
        # Chercher les tableaux de venues
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows[:30]:  # Max 30 venues
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    venue_name = cells[0].get_text(strip=True)
                    venue_sport = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                    
                    if venue_name and len(venue_name) < 100:
                        venues.append({
                            'name': venue_name,
                            'sports': venue_sport,
                            'source': 'wikipedia_venues_page'
                        })
        
        return venues
    
    def scrape_athlete_mentions(self):
        """Cherche des mentions d'athletes dans diverses pages"""
        
        # Pages potentiellement riches en athletes
        athlete_urls = [
            f"{self.base_url}/wiki/France_at_the_2024_Summer_Olympics",
            f"{self.base_url}/wiki/United_States_at_the_2024_Summer_Olympics",
            f"{self.base_url}/wiki/Athletics_at_the_2024_Summer_Olympics"
        ]
        
        all_athletes = []
        
        for url in athlete_urls:
            content = self.fetch_url(url, cache_hours=6)
            if content:
                page_athletes = self.extract_athletes_from_content(content, url)
                all_athletes.extend(page_athletes)
        
        return all_athletes
    
    def extract_athletes_from_content(self, content, source_url):
        """Extrait les noms d'athletes depuis le contenu"""
        soup = BeautifulSoup(content, 'html.parser')
        athletes = []
        
        # Chercher dans les liens vers des profils
        athlete_links = soup.find_all('a', href=True)
        
        for link in athlete_links:
            text = link.get_text(strip=True)
            href = link.get('href')
            
            # Filtrer les noms potentiels d'athletes
            if (self.is_potential_athlete_name(text) and 
                '/wiki/' in href and
                'Category:' not in href and
                'File:' not in href):
                
                athletes.append({
                    'name': text,
                    'wikipedia_url': href if href.startswith('http') else self.base_url + href,
                    'found_on': source_url,
                    'source': 'wikipedia_athlete_link'
                })
        
        return athletes[:100]  # Limiter a 100 par page
    
    def is_potential_athlete_name(self, text):
        """Determine si un texte ressemble a un nom d'athlete"""
        if not text or len(text) < 3 or len(text) > 50:
            return False
        
        words = text.split()
        if len(words) < 2 or len(words) > 4:
            return False
        
        # Doit etre principalement des lettres
        alpha_ratio = sum(c.isalpha() or c.isspace() or c in '-.' for c in text) / len(text)
        if alpha_ratio < 0.8:
            return False
        
        # Doit commencer par une majuscule
        if not text[0].isupper():
            return False
        
        # Eviter les mots communs
        common_words = {'the', 'and', 'or', 'at', 'in', 'on', 'for', 'with', 'by', 'from', 'to', 'of', 'as'}
        if any(word.lower() in common_words for word in words):
            return False
        
        return True
    
    def parse_data(self, raw_data):
        """Transforme les donnees brutes en DataFrame structure"""
        
        all_records = []
        
        # Traiter les sports
        if 'main_page' in raw_data and raw_data['main_page'].get('sports'):
            for sport in raw_data['main_page']['sports']:
                all_records.append({
                    'name': f"SPORT_{sport['name']}",
                    'sport': sport['name'],
                    'country': '',
                    'age': None,
                    'birth_year': None,
                    'profile_url': '',
                    'details': ' | '.join(sport.get('details', [])),
                    'source': 'wikipedia_sports',
                    'scraped_at': datetime.now().isoformat(),
                    'qualified_2024': False,
                    'type': 'sport_reference'
                })
        
        # Traiter les athletes
        if 'athletes' in raw_data:
            for athlete in raw_data['athletes']:
                if isinstance(athlete, dict) and athlete.get('name'):
                    # Eviter les doublons et les faux positifs
                    if (self.is_potential_athlete_name(athlete['name']) and
                        not athlete['name'].startswith('SPORT_')):
                        
                        all_records.append({
                            'name': athlete['name'],
                            'sport': '',  # A determiner plus tard
                            'country': self.extract_country_from_url(athlete.get('found_on', '')),
                            'age': None,
                            'birth_year': None,
                            'profile_url': athlete.get('wikipedia_url', ''),
                            'details': f"Found on: {athlete.get('found_on', '')}",
                            'source': 'wikipedia_athletes',
                            'scraped_at': datetime.now().isoformat(),
                            'qualified_2024': None,  # A determiner
                            'type': 'athlete_mention'
                        })
        
        # Traiter les pays
        if 'main_page' in raw_data and raw_data['main_page'].get('countries'):
            for country in raw_data['main_page']['countries'][:20]:  # Limiter
                all_records.append({
                    'name': f"COUNTRY_{country['name']}",
                    'sport': '',
                    'country': country['name'],
                    'age': None,
                    'birth_year': None,
                    'profile_url': country.get('url', ''),
                    'details': 'Participating country',
                    'source': 'wikipedia_countries',
                    'scraped_at': datetime.now().isoformat(),
                    'qualified_2024': True,  # Les pays sont qualifies
                    'type': 'country_reference'
                })
        
        if not all_records:
            self.logger.warning("No data found to process")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_records)
        
        # Nettoyage
        df = df.drop_duplicates(subset=['name', 'type'], keep='first')
        df = df[df['name'].str.len() > 0]
        
        self.logger.info(f"Processed {len(df)} Wikipedia records")
        return df
    
    def extract_country_from_url(self, url):
        """Extrait le nom du pays depuis une URL"""
        if not url:
            return ''
        
        # Pattern pour les pages de pays aux JO
        country_match = re.search(r'/wiki/([^_]+)_at_the_2024_Summer_Olympics', url)
        if country_match:
            return country_match.group(1).replace('_', ' ')
        
        return ''

if __name__ == "__main__":
    # Test du scraper Wikipedia
    scraper = WikipediaScraper()
    data = scraper.run()
    
    if data is not None and not data.empty:
        print(f"Scraping Wikipedia reussi: {len(data)} enregistrements")
        print()
        print("Repartition par type:")
        print(data['type'].value_counts())
        print()
        print("Sources:")
        print(data['source'].value_counts())
        print()
        print("Exemples d'athletes:")
        athletes_df = data[data['type'] == 'athlete_mention']
        if not athletes_df.empty:
            for _, athlete in athletes_df.head(10).iterrows():
                print(f"  - {athlete['name']} ({athlete['country']})")
        
        print()
        print("Sports identifies:")
        sports_df = data[data['type'] == 'sport_reference']
        if not sports_df.empty:
            for _, sport in sports_df.head(10).iterrows():
                print(f"  - {sport['sport']}")
    else:
        print("Echec du scraping Wikipedia")