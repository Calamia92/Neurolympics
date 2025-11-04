"""
Classe de base pour tous les scrapers olympiques
"""

import requests
import time
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
import logging

class BaseScraper(ABC):
    """Classe de base pour tous les scrapers"""
    
    def __init__(self, name="scraper"):
        self.name = name
        self.session = requests.Session()
        self.rate_limit = 1.0  # secondes entre requetes
        self.cache_dir = Path("data/cache")
        self.raw_data_dir = Path("data/scraped/raw")
        self.processed_data_dir = Path("data/scraped/processed")
        
        # Configuration des headers pour eviter la detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Creer les dossiers necessaires
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True) 
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration du logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"scraper_{self.name}")
    
    def fetch_url(self, url, use_cache=True, cache_hours=24):
        """Recupere une URL avec gestion du cache"""
        
        # Gestion du cache
        if use_cache:
            cache_file = self.cache_dir / f"{self._url_to_filename(url)}.json"
            if cache_file.exists():
                cache_age = time.time() - cache_file.stat().st_mtime
                if cache_age < cache_hours * 3600:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    self.logger.info(f"Cache hit for {url}")
                    return cached_data['content']
        
        # Respecter le rate limit
        time.sleep(self.rate_limit)
        
        try:
            self.logger.info(f"Fetching {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            content = response.text
            
            # Sauvegarder en cache
            if use_cache:
                cache_data = {
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'status_code': response.status_code,
                    'content': content
                }
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return content
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _url_to_filename(self, url):
        """Convertit une URL en nom de fichier valide"""
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()
    
    def save_raw_data(self, data, filename):
        """Sauvegarde les donnees brutes"""
        filepath = self.raw_data_dir / f"{self.name}_{filename}"
        
        if isinstance(data, (dict, list)):
            with open(filepath.with_suffix('.json'), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif isinstance(data, pd.DataFrame):
            data.to_csv(filepath.with_suffix('.csv'), index=False, encoding='utf-8')
        else:
            with open(filepath.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                f.write(str(data))
        
        self.logger.info(f"Raw data saved to {filepath}")
        return filepath
    
    def save_processed_data(self, data, filename):
        """Sauvegarde les donnees traitees"""
        filepath = self.processed_data_dir / f"{self.name}_{filename}"
        
        if isinstance(data, pd.DataFrame):
            data.to_csv(filepath.with_suffix('.csv'), index=False, encoding='utf-8')
            self.logger.info(f"Processed data saved to {filepath}")
            return filepath
        else:
            self.logger.error("Processed data must be a DataFrame")
            return None
    
    @abstractmethod
    def scrape(self):
        """Methode principale de scraping a implementer"""
        pass
    
    @abstractmethod
    def parse_data(self, raw_data):
        """Parse les donnees brutes en format structure"""
        pass
    
    def run(self):
        """Execute le pipeline complet de scraping"""
        self.logger.info(f"Starting {self.name} scraper")
        start_time = time.time()
        
        try:
            # Scraping
            raw_data = self.scrape()
            if raw_data is None:
                self.logger.error("Scraping failed - no data returned")
                return None
            
            # Sauvegarde des donnees brutes
            self.save_raw_data(raw_data, f"raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Traitement
            processed_data = self.parse_data(raw_data)
            if processed_data is None or processed_data.empty:
                self.logger.error("Data parsing failed - no processed data")
                return None
            
            # Sauvegarde des donnees traitees
            filepath = self.save_processed_data(processed_data, f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            duration = time.time() - start_time
            self.logger.info(f"Scraping completed in {duration:.2f}s - {len(processed_data)} records extracted")
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return None
    
    def get_latest_data(self):
        """Recupere les dernieres donnees traitees"""
        pattern = f"{self.name}_processed_*.csv"
        files = list(self.processed_data_dir.glob(pattern))
        
        if not files:
            self.logger.info("No processed data found")
            return None
        
        # Prendre le fichier le plus recent
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        
        try:
            df = pd.read_csv(latest_file, encoding='utf-8')
            self.logger.info(f"Loaded {len(df)} records from {latest_file.name}")
            return df
        except Exception as e:
            self.logger.error(f"Error loading data from {latest_file}: {e}")
            return None