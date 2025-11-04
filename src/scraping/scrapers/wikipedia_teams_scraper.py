"""
Scraper specialise pour les pages Wikipedia d'equipes nationales JO 2024
Ces pages contiennent des listes completes et structurees d'athletes
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

class WikipediaTeamsScraper(BaseScraper):
    """Scraper pour equipes nationales sur Wikipedia - structure fiable"""
    
    def __init__(self):
        super().__init__("wikipedia_teams")
        self.base_url = "https://en.wikipedia.org"
        self.rate_limit = 1.0
    
    def scrape(self):
        """Scrape les principales equipes nationales sur Wikipedia"""
        
        # Top countries avec pages Wikipedia detaillees
        team_pages = [
            ('United States', 'United_States_at_the_2024_Summer_Olympics'),
            ('France', 'France_at_the_2024_Summer_Olympics'), 
            ('Great Britain', 'Great_Britain_at_the_2024_Summer_Olympics'),
            ('Germany', 'Germany_at_the_2024_Summer_Olympics'),
            ('Italy', 'Italy_at_the_2024_Summer_Olympics'),
            ('Australia', 'Australia_at_the_2024_Summer_Olympics'),
            ('Japan', 'Japan_at_the_2024_Summer_Olympics'),
            ('Canada', 'Canada_at_the_2024_Summer_Olympics'),
            ('Netherlands', 'Netherlands_at_the_2024_Summer_Olympics'),
            ('Spain', 'Spain_at_the_2024_Summer_Olympics'),
            ('China', 'China_at_the_2024_Summer_Olympics'),
            ('Brazil', 'Brazil_at_the_2024_Summer_Olympics')
        ]
        
        scraped_data = {}
        
        for country, page_name in team_pages:
            self.logger.info(f"Scraping {country} team page")
            country_athletes = self.scrape_country_team(country, page_name)
            scraped_data[country.lower().replace(' ', '_')] = country_athletes
        
        return scraped_data
    
    def scrape_country_team(self, country_name, page_name):
        """Scrape une page d'equipe nationale specifique"""
        url = f"{self.base_url}/wiki/{page_name}"
        
        content = self.fetch_url(url, cache_hours=8)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        athletes = []
        
        # Methode 1: Chercher sections "Competitors" ou "Athletes"
        competitors_section = soup.find(['h2', 'h3'], string=re.compile(r'Competitors|Athletes|Team|Squad', re.IGNORECASE))
        if competitors_section:
            athletes.extend(self.extract_athletes_from_section(competitors_section, country_name))
        
        # Methode 2: Chercher tableaux par sport
        sport_tables = self.find_sport_tables(soup, country_name)
        athletes.extend(sport_tables)
        
        # Methode 3: Chercher listes d'athletes
        athlete_lists = self.find_athlete_lists(soup, country_name)
        athletes.extend(athlete_lists)
        
        return athletes[:500]  # Max 500 par pays
    
    def extract_athletes_from_section(self, section, country_name):
        """Extrait athletes depuis une section specifique"""
        athletes = []
        
        # Chercher le contenu apres la section
        next_content = section.find_next_sibling()
        
        # Parcourir le contenu jusqu'a la prochaine section
        while next_content and next_content.name not in ['h1', 'h2', 'h3']:
            
            if next_content.name == 'table':
                table_athletes = self.extract_athletes_from_table(next_content, country_name)
                athletes.extend(table_athletes)
            
            elif next_content.name in ['ul', 'ol']:
                list_athletes = self.extract_athletes_from_list(next_content, country_name)
                athletes.extend(list_athletes)
            
            elif next_content.name == 'div':
                # Chercher sous-tableaux dans les divs
                sub_tables = next_content.find_all('table')
                for table in sub_tables:
                    table_athletes = self.extract_athletes_from_table(table, country_name)
                    athletes.extend(table_athletes)
            
            next_content = next_content.find_next_sibling()
        
        return athletes
    
    def find_sport_tables(self, soup, country_name):
        """Trouve tableaux organises par sport"""
        athletes = []
        
        # Chercher headers de sports
        sport_headers = soup.find_all(['h3', 'h4'], string=re.compile(
            r'Athletics|Swimming|Gymnastics|Tennis|Basketball|Football|Volleyball|Cycling|Boxing|Judo|Wrestling|Rowing|Sailing|Shooting|Archery|Badminton|Table tennis|Weightlifting|Taekwondo|Fencing|Equestrian|Triathlon|Golf|Rugby|Surfing|Skateboarding|Sport climbing|Karate|Baseball|Softball',
            re.IGNORECASE
        ))
        
        for header in sport_headers:
            sport_name = header.get_text(strip=True)
            sport_name = re.sub(r'\\[edit\\]', '', sport_name).strip()
            
            # Chercher tableau suivant
            next_table = header.find_next('table', {'class': 'wikitable'})
            if next_table:
                sport_athletes = self.extract_athletes_from_table(next_table, country_name, sport_name)
                athletes.extend(sport_athletes)
        
        return athletes
    
    def find_athlete_lists(self, soup, country_name):
        """Trouve listes simples d'athletes"""
        athletes = []
        
        # Chercher listes avec beaucoup de liens vers athletes
        lists = soup.find_all(['ul', 'ol'])
        
        for list_elem in lists:
            items = list_elem.find_all('li')
            
            # Si plus de 5 items qui ressemblent a des athletes
            athlete_count = 0
            list_athletes = []
            
            for item in items:
                links = item.find_all('a')
                for link in links:
                    text = link.get_text(strip=True)
                    if self.is_potential_athlete_name(text):
                        athlete_count += 1
                        list_athletes.append({
                            'name': text,
                            'sport': '',
                            'country': country_name,
                            'profile_url': self.make_absolute_url(link.get('href', '')),
                            'source_context': 'wikipedia_athlete_list'
                        })
            
            # Si au moins 10 athletes dans la liste, c'est probablement une liste d'equipe
            if athlete_count >= 10:
                athletes.extend(list_athletes[:100])  # Max 100 par liste
        
        return athletes
    
    def extract_athletes_from_table(self, table, country_name, sport_name=''):
        """Extrait athletes depuis tableau Wikipedia"""
        athletes = []
        
        # Analyser les headers pour comprendre la structure
        headers = []
        header_row = table.find('tr')
        if header_row:
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        
        # Identifier colonnes importantes
        name_col = self.find_column_index(headers, ['athlete', 'name', 'competitor'])
        event_col = self.find_column_index(headers, ['event', 'discipline', 'sport'])
        
        rows = table.find_all('tr')[1:]  # Skip header
        
        for row in rows[:100]:  # Max 100 par tableau
            cells = row.find_all(['td', 'th'])
            
            if len(cells) >= 2:
                athlete_info = self.extract_athlete_from_table_row(
                    cells, country_name, sport_name, name_col, event_col
                )
                if athlete_info:
                    athletes.append(athlete_info)
        
        return athletes
    
    def extract_athletes_from_list(self, list_elem, country_name):
        """Extrait athletes depuis liste"""
        athletes = []
        
        items = list_elem.find_all('li')
        for item in items[:50]:  # Max 50 par liste
            
            # Chercher liens d'athletes
            links = item.find_all('a')
            for link in links:
                text = link.get_text(strip=True)
                href = link.get('href', '')
                
                if self.is_potential_athlete_name(text) and '/wiki/' in href:
                    athletes.append({
                        'name': text,
                        'sport': '',
                        'country': country_name,
                        'profile_url': self.make_absolute_url(href),
                        'source_context': 'wikipedia_list_item'
                    })
        
        return athletes
    
    def extract_athlete_from_table_row(self, cells, country_name, sport_name, name_col, event_col):
        """Extrait athlete depuis ligne de tableau"""
        athlete_name = ''
        event = sport_name
        additional_info = []
        
        for i, cell in enumerate(cells):
            text = cell.get_text(strip=True)
            text = re.sub(r'\\[.*?\\]', '', text).strip()
            
            # Si on a identifie la colonne nom
            if name_col is not None and i == name_col:
                if self.is_potential_athlete_name(text):
                    athlete_name = text
            
            # Si on a identifie la colonne event
            elif event_col is not None and i == event_col:
                event = text
            
            # Sinon, chercher le nom dans les premieres colonnes
            elif i < 3 and not athlete_name:
                # Chercher liens d'athletes
                links = cell.find_all('a')
                for link in links:
                    link_text = link.get_text(strip=True)
                    if self.is_potential_athlete_name(link_text):
                        athlete_name = link_text
                        break
                
                # Fallback: texte brut
                if not athlete_name and self.is_potential_athlete_name(text):
                    athlete_name = text
            
            # Collecter info additionnelle
            else:
                if text and len(text) < 100:
                    additional_info.append(text)
        
        if athlete_name and len(athlete_name) > 2:
            return {
                'name': athlete_name,
                'sport': event or sport_name,
                'country': country_name,
                'profile_url': '',
                'additional_info': ' | '.join(additional_info),
                'source_context': 'wikipedia_team_table'
            }
        
        return None
    
    def find_column_index(self, headers, keywords):
        """Trouve l'index d'une colonne basee sur mots-cles"""
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in keywords):
                return i
        return None
    
    def make_absolute_url(self, href):
        """Convertit URL relative en absolue"""
        if href and not href.startswith('http'):
            if href.startswith('/'):
                return self.base_url + href
        return href
    
    def is_potential_athlete_name(self, text):
        """Determine si texte est un nom athlete (version stricte pour Wikipedia)"""
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
        
        # Eviter faux positifs Wikipedia specifiques
        false_positives = {
            'Main Page', 'Wikipedia', 'Category', 'Template', 'File', 'Talk',
            'User', 'Project', 'Help', 'Special', 'Media',
            'Summer Olympics', 'Olympic Games', 'Paris 2024', 'Tokyo 2020',
            'World Championships', 'European Championships', 'Commonwealth Games',
            'See Also', 'References', 'External Links', 'Further Reading',
            'Edit', 'View', 'History', 'What Links Here'
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
        
        # Traiter chaque pays
        for country_key, athletes_list in raw_data.items():
            if athletes_list:
                country_name = country_key.replace('_', ' ').title()
                
                for athlete in athletes_list:
                    if isinstance(athlete, dict) and athlete.get('name'):
                        record = {
                            'name': athlete['name'],
                            'sport': athlete.get('sport', ''),
                            'country': athlete.get('country', country_name),
                            'age': None,
                            'birth_year': None,
                            'profile_url': athlete.get('profile_url', ''),
                            'details': athlete.get('additional_info', ''),
                            'source': f'wikipedia_teams_{country_key}',
                            'scraped_at': datetime.now().isoformat(),
                            'qualified_2024': True,  # Athletes d'equipes nationales = qualifies
                            'type': 'national_team_wikipedia'
                        }
                        all_athletes.append(record)
        
        if not all_athletes:
            self.logger.warning("No Wikipedia team athletes found")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_athletes)
        
        # Nettoyage et deduplication
        df = df.drop_duplicates(subset=['name', 'country'], keep='first')
        df = df[df['name'].str.len() > 2]
        
        # Filtrer faux positifs
        df = df[~df['name'].str.contains('Olympics|Games|Championship|Medal|Event|Final', case=False, na=False)]
        
        self.logger.info(f"Processed {len(df)} Wikipedia team athletes")
        return df

if __name__ == "__main__":
    # Test du scraper Wikipedia teams
    scraper = WikipediaTeamsScraper()
    data = scraper.run()
    
    if data is not None and not data.empty:
        print(f"Scraping Wikipedia Teams reussi: {len(data)} athletes d'equipes")
        print()
        print("Repartition par pays:")
        print(data['country'].value_counts())
        print()
        print("Repartition par sport:")
        print(data['sport'].value_counts().head(10))
        print()
        print("Exemples athletes par equipe:")
        for country in data['country'].unique()[:5]:
            country_athletes = data[data['country'] == country]
            print(f"\\n{country} ({len(country_athletes)} athletes):")
            for _, athlete in country_athletes.head(5).iterrows():
                print(f"  - {athlete['name']} ({athlete['sport']})")
    else:
        print("Echec du scraping Wikipedia Teams")