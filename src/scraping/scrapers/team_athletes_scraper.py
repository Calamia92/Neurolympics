"""
Scraper specialise pour recuperer les listes completes d'athletes
depuis les equipes nationales et federations sportives internationales
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

class TeamAthletesScraper(BaseScraper):
    """Scraper pour equipes nationales et federations sportives"""
    
    def __init__(self):
        super().__init__("team_athletes")
        self.rate_limit = 2.0  # Respectueux pour sites officiels
    
    def scrape(self):
        """Scrape plusieurs sources d'equipes et federations"""
        
        scraped_data = {
            'team_usa': self.scrape_team_usa(),
            'team_france': self.scrape_team_france(),
            'team_gb': self.scrape_team_gb(),
            'world_athletics': self.scrape_world_athletics(),
            'olympic_channel': self.scrape_olympic_channel(),
            'ioc_database': self.scrape_ioc_database()
        }
        
        return scraped_data
    
    def scrape_team_usa(self):
        """Scrape Team USA - source la plus riche"""
        url = "https://www.teamusa.org/"
        
        content = self.fetch_url(url, cache_hours=6)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        athletes = []
        
        # Chercher liens vers athletes ou rosters
        athlete_links = soup.find_all('a', href=re.compile(r'athlete|roster|team|sport', re.IGNORECASE))
        
        for link in athlete_links[:50]:  # Limiter pour eviter surcharge
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if href and not href.startswith('http'):
                href = 'https://www.teamusa.org' + href
            
            # Si ca ressemble a un profil athlete
            if self.is_athlete_profile_link(href, text):
                athlete_info = self.extract_athlete_from_link(link, 'team_usa')
                if athlete_info:
                    athletes.append(athlete_info)
        
        # Chercher aussi dans les listes/tableaux
        tables = soup.find_all('table')
        for table in tables:
            table_athletes = self.extract_athletes_from_table(table, 'team_usa')
            athletes.extend(table_athletes)
        
        return athletes[:200]  # Max 200 pour Team USA
    
    def scrape_team_france(self):
        """Scrape Team France"""
        url = "https://www.franceolympique.com/"
        
        content = self.fetch_url(url, cache_hours=6)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        athletes = []
        
        # Chercher sections athletes/equipes
        athlete_sections = soup.find_all(['div', 'section'], class_=re.compile(r'athlete|equipe|sport', re.IGNORECASE))
        
        for section in athlete_sections:
            links = section.find_all('a', href=True)
            for link in links[:30]:
                athlete_info = self.extract_athlete_from_link(link, 'team_france')
                if athlete_info:
                    athlete_info['country'] = 'France'  # Force le pays
                    athletes.append(athlete_info)
        
        return athletes[:150]
    
    def scrape_team_gb(self):
        """Scrape Team GB"""
        url = "https://www.teamgb.com/"
        
        content = self.fetch_url(url, cache_hours=6)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        athletes = []
        
        # Team GB structure typique
        athlete_cards = soup.find_all(['div', 'article'], class_=re.compile(r'athlete|profile|card', re.IGNORECASE))
        
        for card in athlete_cards:
            athlete_info = self.extract_athlete_from_card(card, 'team_gb')
            if athlete_info:
                athlete_info['country'] = 'Great Britain'
                athletes.append(athlete_info)
        
        return athletes[:100]
    
    def scrape_world_athletics(self):
        """Scrape World Athletics pour les qualifies"""
        url = "https://worldathletics.org/competitions/olympic-games/paris24"
        
        content = self.fetch_url(url, cache_hours=4)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        athletes = []
        
        # Chercher listes de qualifies
        qualified_sections = soup.find_all(['div', 'section'], string=re.compile(r'qualified|entries|competitors', re.IGNORECASE))
        
        for section in qualified_sections:
            # Chercher le contenu suivant
            next_content = section.find_next(['table', 'ul', 'div'])
            if next_content:
                section_athletes = self.extract_athletes_from_element(next_content, 'world_athletics')
                athletes.extend(section_athletes)
        
        return athletes[:300]  # Athletics a beaucoup d'athletes
    
    def scrape_olympic_channel(self):
        """Scrape Olympic Channel athletes"""
        url = "https://www.olympicchannel.com/en/athletes/"
        
        content = self.fetch_url(url, cache_hours=6)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        athletes = []
        
        # Structure Olympic Channel
        athlete_profiles = soup.find_all('a', href=re.compile(r'/athletes/', re.IGNORECASE))
        
        for profile in athlete_profiles[:100]:
            athlete_info = self.extract_athlete_from_link(profile, 'olympic_channel')
            if athlete_info:
                athletes.append(athlete_info)
        
        return athletes
    
    def scrape_ioc_database(self):
        """Scrape IOC official database"""
        url = "https://olympics.com/en/athletes"
        
        content = self.fetch_url(url, cache_hours=6)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        athletes = []
        
        # Structure IOC
        athlete_entries = soup.find_all(['div', 'article'], class_=re.compile(r'athlete|profile', re.IGNORECASE))
        
        for entry in athlete_entries[:150]:
            athlete_info = self.extract_athlete_from_card(entry, 'ioc_official')
            if athlete_info:
                athletes.append(athlete_info)
        
        return athletes
    
    def is_athlete_profile_link(self, href, text):
        """Determine si un lien pointe vers un profil athlete"""
        if not href or not text:
            return False
        
        # Patterns de liens athletes
        athlete_patterns = [r'/athlete/', r'/profile/', r'/player/', r'/competitor/', r'/bio/']
        
        for pattern in athlete_patterns:
            if re.search(pattern, href, re.IGNORECASE):
                return True
        
        # Si le texte ressemble a un nom
        return self.is_potential_athlete_name(text)
    
    def extract_athlete_from_link(self, link, source):
        """Extrait info athlete depuis un lien"""
        text = link.get_text(strip=True)
        href = link.get('href', '')
        
        if not self.is_potential_athlete_name(text):
            return None
        
        # Chercher sport/pays dans contexte
        sport = self.extract_sport_from_context(link)
        country = self.extract_country_from_context(link)
        
        return {
            'name': text,
            'sport': sport,
            'country': country,
            'profile_url': href if href.startswith('http') else '',
            'source_context': source,
            'extraction_method': 'link_analysis'
        }
    
    def extract_athlete_from_card(self, card, source):
        """Extrait info athlete depuis une carte/div"""
        # Chercher le nom
        name_elem = card.find(['h1', 'h2', 'h3', 'h4', '.name', '.athlete-name'])
        if not name_elem:
            # Fallback: premier lien ou texte
            name_elem = card.find('a') or card
        
        name = name_elem.get_text(strip=True) if name_elem else ''
        
        if not self.is_potential_athlete_name(name):
            return None
        
        # Chercher sport
        sport_elem = card.find(string=re.compile(r'sport|discipline', re.IGNORECASE))
        sport = sport_elem.strip() if sport_elem else ''
        
        # Chercher pays
        country_elem = card.find(['span', 'div'], class_=re.compile(r'country|nation', re.IGNORECASE))
        country = country_elem.get_text(strip=True) if country_elem else ''
        
        return {
            'name': name,
            'sport': sport,
            'country': country,
            'profile_url': '',
            'source_context': source,
            'extraction_method': 'card_analysis'
        }
    
    def extract_athletes_from_table(self, table, source):
        """Extrait athletes depuis tableau"""
        athletes = []
        rows = table.find_all('tr')[1:]  # Skip header
        
        for row in rows[:50]:  # Limiter
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                athlete_info = self.extract_athlete_from_row(cells, source)
                if athlete_info:
                    athletes.append(athlete_info)
        
        return athletes
    
    def extract_athletes_from_element(self, element, source):
        """Extrait athletes depuis element generique"""
        athletes = []
        
        # Si c'est une liste
        if element.name == 'ul':
            items = element.find_all('li')
            for item in items[:30]:
                text = item.get_text(strip=True)
                if self.is_potential_athlete_name(text):
                    athletes.append({
                        'name': text,
                        'sport': '',
                        'country': '',
                        'source_context': source,
                        'extraction_method': 'list_item'
                    })
        
        # Si c'est un tableau
        elif element.name == 'table':
            athletes.extend(self.extract_athletes_from_table(element, source))
        
        return athletes
    
    def extract_athlete_from_row(self, cells, source):
        """Extrait athlete depuis ligne tableau (herite de athletes_2024_scraper)"""
        athlete_name = ''
        country = ''
        sport = ''
        additional_info = []
        
        for i, cell in enumerate(cells[:4]):
            text = cell.get_text(strip=True)
            text = re.sub(r'\\[.*?\\]', '', text).strip()
            
            if i == 0 and self.is_potential_athlete_name(text):
                athlete_name = text
            elif i == 1:
                if self.is_potential_country(text):
                    country = text
                elif not athlete_name and self.is_potential_athlete_name(text):
                    athlete_name = text
            elif i == 2 and not sport:
                sport = text
            else:
                if text and len(text) < 100:
                    additional_info.append(text)
        
        if athlete_name and len(athlete_name) > 2:
            return {
                'name': athlete_name,
                'country': country,
                'sport': sport,
                'additional_info': ' | '.join(additional_info),
                'source_context': source,
                'extraction_method': 'table_row'
            }
        
        return None
    
    def extract_sport_from_context(self, element):
        """Extrait sport depuis contexte de l'element"""
        # Chercher dans les parents
        parent = element.parent
        for _ in range(3):  # Max 3 niveaux
            if parent:
                text = parent.get_text().lower()
                sports_keywords = ['athletics', 'swimming', 'gymnastics', 'tennis', 'basketball', 
                                 'football', 'volleyball', 'cycling', 'rowing', 'boxing']
                for sport in sports_keywords:
                    if sport in text:
                        return sport.title()
                parent = parent.parent
        return ''
    
    def extract_country_from_context(self, element):
        """Extrait pays depuis contexte de l'element"""
        # Chercher dans les classes et attributs
        for _ in range(2):
            if element:
                classes = element.get('class', [])
                for cls in classes:
                    if any(country in cls.lower() for country in ['usa', 'france', 'britain', 'germany']):
                        return cls.title()
                element = element.parent
        return ''
    
    def is_potential_country(self, text):
        """Determine si texte est un pays (herite)"""
        if not text or len(text) < 2 or len(text) > 30:
            return False
        
        country_codes = ['USA', 'FRA', 'GBR', 'GER', 'ITA', 'ESP', 'CAN', 'AUS', 'JPN', 'CHN']
        if text.upper() in country_codes:
            return True
        
        countries = ['United States', 'France', 'Great Britain', 'Germany', 'Italy', 
                    'Spain', 'Canada', 'Australia', 'Japan', 'China']
        return any(country.lower() in text.lower() for country in countries)
    
    def is_potential_athlete_name(self, text):
        """Determine si texte est un nom athlete (improved version)"""
        if not text or len(text) < 3 or len(text) > 50:
            return False
        
        words = text.split()
        if len(words) < 2 or len(words) > 4:
            return False
        
        # Doit etre principalement des lettres
        alpha_ratio = sum(c.isalpha() or c.isspace() or c in '-.\'' for c in text) / len(text)
        if alpha_ratio < 0.8:
            return False
        
        # Doit commencer par une majuscule
        if not text[0].isupper():
            return False
        
        # Eviter faux positifs specifiques aux sites d'equipes
        false_positives = {
            'Team USA', 'Team France', 'Team GB', 'Olympic Games', 'Paris 2024',
            'World Athletics', 'Learn More', 'Read More', 'View All', 'See More',
            'Latest News', 'Breaking News', 'Live Stream', 'Watch Now',
            'Sign Up', 'Log In', 'Contact Us', 'About Us', 'Privacy Policy'
        }
        if any(fp.lower() in text.lower() for fp in false_positives):
            return False
        
        # Eviter mots communs
        common_words = {'the', 'and', 'or', 'at', 'in', 'on', 'for', 'with', 'by', 'from', 'to', 'of', 'as'}
        if any(word.lower() in common_words for word in words):
            return False
        
        return True
    
    def parse_data(self, raw_data):
        """Transforme donnees brutes en DataFrame structure"""
        
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
                            'profile_url': athlete.get('profile_url', ''),
                            'details': athlete.get('additional_info', ''),
                            'source': f'team_athletes_{source_name}',
                            'scraped_at': datetime.now().isoformat(),
                            'qualified_2024': True,  # Athletes d'equipes = qualifies
                            'type': 'national_team_athlete'
                        }
                        all_athletes.append(record)
        
        if not all_athletes:
            self.logger.warning("No team athletes found")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_athletes)
        
        # Nettoyage et deduplication
        df = df.drop_duplicates(subset=['name', 'country'], keep='first')
        df = df[df['name'].str.len() > 2]
        
        # Filtrer faux positifs
        df = df[~df['name'].str.contains('Team|Olympic|News|More|View|Watch', case=False, na=False)]
        
        self.logger.info(f"Processed {len(df)} team athletes")
        return df

if __name__ == "__main__":
    # Test du scraper equipes
    scraper = TeamAthletesScraper()
    data = scraper.run()
    
    if data is not None and not data.empty:
        print(f"Scraping Team Athletes reussi: {len(data)} athletes d'equipes")
        print()
        print("Repartition par source:")
        print(data['source'].value_counts())
        print()
        print("Repartition par pays:")
        print(data['country'].value_counts().head(10))
        print()
        print("Exemples athletes d'equipes:")
        for _, athlete in data.head(15).iterrows():
            print(f"  - {athlete['name']} ({athlete['sport']}, {athlete['country']})")
    else:
        print("Echec du scraping Team Athletes")