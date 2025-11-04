"""
Scraper pour olympics.com (site officiel IOC)
Recupere les informations sur les athletes et competitions olympiques
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

class OlympicsScraper(BaseScraper):
    """Scraper pour olympics.com"""
    
    def __init__(self):
        super().__init__("olympics")
        self.base_url = "https://olympics.com"
        self.rate_limit = 1.5
        
        # Configuration SSL plus permissive
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        self.session = requests.Session()
        
        # Configuration des retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Headers plus complets
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def scrape(self):
        """Scrape les principales pages d'olympics.com"""
        
        scraped_data = {
            'athletes': self.scrape_athletes_list(),
            'sports': self.scrape_sports_list(),
            'news': self.scrape_news()
        }
        
        return scraped_data
    
    def scrape_athletes_list(self):
        """Recupere une liste d'athletes depuis olympics.com"""
        
        # Pages d'athletes potentielles
        athlete_urls = [
            f"{self.base_url}/en/athletes",
            f"{self.base_url}/en/paris-2024/athletes",
            f"{self.base_url}/en/athletes/all"
        ]
        
        athletes_data = []
        
        for url in athlete_urls:
            self.logger.info(f"Scraping athletes from {url}")
            content = self.fetch_url(url, use_cache=True, cache_hours=6)
            
            if content:
                page_athletes = self.parse_athletes_page(content, url)
                athletes_data.extend(page_athletes)
                
                # Chercher des liens vers d'autres pages d'athletes
                additional_links = self.find_athlete_links(content)
                
                # Limiter a 10 pages supplementaires pour eviter trop de requetes
                for link in additional_links[:10]:
                    full_url = link if link.startswith('http') else self.base_url + link
                    if full_url not in athlete_urls:
                        additional_content = self.fetch_url(full_url, use_cache=True, cache_hours=6)
                        if additional_content:
                            athletes_data.extend(self.parse_athletes_page(additional_content, full_url))
        
        # Deduplication
        unique_athletes = []
        seen_names = set()
        
        for athlete in athletes_data:
            name = athlete.get('name', '').strip().lower()
            if name and name not in seen_names:
                seen_names.add(name)
                unique_athletes.append(athlete)
        
        self.logger.info(f"Found {len(unique_athletes)} unique athletes")
        return unique_athletes
    
    def find_athlete_links(self, content):
        """Trouve des liens vers des profils d'athletes"""
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        
        # Chercher des liens contenant "athlete" dans l'URL
        for link in soup.find_all('a', href=True):
            href = link['href']
            if re.search(r'/athletes?/', href) or re.search(r'/profil', href):
                links.append(href)
        
        return list(set(links))  # Dedupliquer
    
    def parse_athletes_page(self, content, source_url):
        """Parse une page d'athletes"""
        soup = BeautifulSoup(content, 'html.parser')
        athletes = []
        
        # Patterns de recherche d'athletes
        athlete_selectors = [
            'div[class*="athlete"]',
            'div[class*="player"]',
            'article[class*="athlete"]',
            '.athlete-card',
            '.athlete-item',
            '.player-card',
            '[data-athlete]'
        ]
        
        for selector in athlete_selectors:
            elements = soup.select(selector)
            
            for element in elements:
                athlete_info = self.extract_athlete_info(element)
                if athlete_info and athlete_info.get('name'):
                    athlete_info['source_url'] = source_url
                    athlete_info['scraped_at'] = datetime.now().isoformat()
                    athletes.append(athlete_info)
        
        # Si aucun athlete trouve avec les selectors, chercher dans le texte
        if not athletes:
            athletes = self.extract_athletes_from_text(content, source_url)
        
        return athletes
    
    def extract_athlete_info(self, element):
        """Extrait les informations d'un element athlete"""
        info = {}
        
        # Nom de l'athlete
        name_selectors = ['h1', 'h2', 'h3', 'h4', '.name', '.athlete-name', '.title', '.player-name']
        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                name = name_elem.get_text(strip=True)
                if len(name.split()) >= 2:  # Au moins prenom nom
                    info['name'] = name
                    break
        
        # Sport/Discipline
        sport_selectors = ['.sport', '.discipline', '.category', '.event']
        for selector in sport_selectors:
            sport_elem = element.select_one(selector)
            if sport_elem:
                info['sport'] = sport_elem.get_text(strip=True)
                break
        
        # Pays/Nationalite
        country_selectors = ['.country', '.nationality', '.nation', '.flag', '.team']
        for selector in country_selectors:
            country_elem = element.select_one(selector)
            if country_elem:
                country_text = country_elem.get_text(strip=True)
                # Nettoyer le texte du pays
                country_text = re.sub(r'[^a-zA-Z\s]', '', country_text).strip()
                if country_text:
                    info['country'] = country_text
                    break
        
        # URL du profil
        profile_link = element.find('a', href=True)
        if profile_link:
            href = profile_link['href']
            info['profile_url'] = href if href.startswith('http') else self.base_url + href
        
        # Informations supplementaires dans le texte
        element_text = element.get_text()
        
        # Age ou annee de naissance
        age_match = re.search(r'(\d{1,2})\s*years?\s*old|aged?\s*(\d{1,2})', element_text, re.IGNORECASE)
        birth_match = re.search(r'born\s*(\d{4})|birth\s*(\d{4})|(\d{4})\s*born', element_text, re.IGNORECASE)
        
        if age_match:
            age = int(age_match.group(1) or age_match.group(2))
            info['age'] = age
            info['birth_year'] = 2024 - age
        elif birth_match:
            birth_year = int(birth_match.group(1) or birth_match.group(2) or birth_match.group(3))
            info['birth_year'] = birth_year
            info['age'] = 2024 - birth_year
        
        # Medailles ou achievements
        medals_match = re.search(r'(\d+)\s*(gold|silver|bronze|medal)', element_text, re.IGNORECASE)
        if medals_match:
            info['medals_info'] = f"{medals_match.group(1)} {medals_match.group(2)}"
        
        return info if info.get('name') else None
    
    def extract_athletes_from_text(self, content, source_url):
        """Extrait les athletes depuis le texte brut si les selectors echouent"""
        soup = BeautifulSoup(content, 'html.parser')
        athletes = []
        
        # Chercher tous les liens contenant des noms potentiels
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = link['href']
            
            # Verifier si c'est un nom d'athlete (au moins 2 mots, lettres principalement)
            if (len(text.split()) >= 2 and 
                len(text) <= 50 and 
                re.match(r'^[A-Za-z\s\'-\.]+$', text) and
                ('athlete' in href.lower() or 'profil' in href.lower())):
                
                athletes.append({
                    'name': text,
                    'profile_url': href if href.startswith('http') else self.base_url + href,
                    'source_url': source_url,
                    'scraped_at': datetime.now().isoformat()
                })
        
        return athletes[:100]  # Limiter pour eviter le spam
    
    def scrape_sports_list(self):
        """Recupere la liste des sports"""
        sports_url = f"{self.base_url}/en/sports"
        
        content = self.fetch_url(sports_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        sports = []
        
        # Chercher les liens vers les sports
        sport_links = soup.find_all('a', href=re.compile(r'/sports?/'))
        
        for link in sport_links:
            sport_name = link.get_text(strip=True)
            sport_url = link['href']
            
            if sport_name and len(sport_name) > 2:
                sports.append({
                    'name': sport_name,
                    'url': sport_url if sport_url.startswith('http') else self.base_url + sport_url,
                    'scraped_at': datetime.now().isoformat()
                })
        
        # Deduplication
        unique_sports = []
        seen_names = set()
        
        for sport in sports:
            name = sport['name'].lower()
            if name not in seen_names:
                seen_names.add(name)
                unique_sports.append(sport)
        
        self.logger.info(f"Found {len(unique_sports)} sports")
        return unique_sports
    
    def scrape_news(self):
        """Recupere les actualites pour avoir du contexte"""
        news_url = f"{self.base_url}/en/news"
        
        content = self.fetch_url(news_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        news_items = []
        
        # Chercher les articles
        article_selectors = ['article', '.news-item', '.article', 'div[class*="news"]']
        
        for selector in article_selectors:
            articles = soup.select(selector)
            
            for article in articles[:20]:  # Limiter a 20 articles
                title_elem = article.select_one('h1, h2, h3, .title, .headline')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    
                    # Chercher un lien
                    link_elem = article.find('a', href=True)
                    article_url = ''
                    if link_elem:
                        href = link_elem['href']
                        article_url = href if href.startswith('http') else self.base_url + href
                    
                    news_items.append({
                        'title': title,
                        'url': article_url,
                        'scraped_at': datetime.now().isoformat()
                    })
        
        self.logger.info(f"Found {len(news_items)} news items")
        return news_items
    
    def parse_data(self, raw_data):
        """Transforme les donnees brutes en DataFrame"""
        
        athletes_list = []
        
        # Traitement des athletes
        if 'athletes' in raw_data and raw_data['athletes']:
            for athlete in raw_data['athletes']:
                if isinstance(athlete, dict) and athlete.get('name'):
                    athletes_list.append({
                        'name': athlete.get('name', ''),
                        'sport': athlete.get('sport', ''),
                        'country': athlete.get('country', ''),
                        'age': athlete.get('age'),
                        'birth_year': athlete.get('birth_year'),
                        'profile_url': athlete.get('profile_url', ''),
                        'medals_info': athlete.get('medals_info', ''),
                        'source': 'olympics.com',
                        'scraped_at': athlete.get('scraped_at', datetime.now().isoformat()),
                        'qualified_2024': None  # A determiner
                    })
        
        if not athletes_list:
            self.logger.warning("No athletes data found to process")
            return pd.DataFrame()
        
        df = pd.DataFrame(athletes_list)
        
        # Nettoyage
        df = df.drop_duplicates(subset=['name'], keep='first')
        df = df[df['name'].str.len() > 0]
        
        # Nettoyage des noms
        df['name'] = df['name'].str.strip()
        df['name'] = df['name'].str.title()
        
        self.logger.info(f"Processed {len(df)} athlete records")
        return df

if __name__ == "__main__":
    # Test du scraper
    scraper = OlympicsScraper()
    data = scraper.run()
    
    if data is not None and not data.empty:
        print(f"Scraping successful: {len(data)} records")
        print("\nFirst 5 records:")
        print(data.head())
        
        print(f"\nColumns: {list(data.columns)}")
        if 'country' in data.columns:
            print(f"Countries: {data['country'].value_counts().head()}")
        if 'sport' in data.columns:
            print(f"Sports: {data['sport'].value_counts().head()}")
    else:
        print("Scraping failed or no data found")