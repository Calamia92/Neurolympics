"""
Analyseur de donnees olympiques pour identifier les patterns historiques
Base pour les modeles predictifs Paris 2024
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.connection import get_db_connection
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import re

class OlympicsDataAnalyzer:
    """Classe pour analyser les patterns des donnees olympiques"""
    
    def __init__(self):
        self.db = get_db_connection()
        self.historical_data = None
        self.scraped_data = None
        
    def load_data(self):
        """Charge toutes les donnees necessaires"""
        print("Chargement des donnees...")
        
        # Donnees historiques
        historical_query = """
        SELECT 
            r.country_name,
            r.medal_type,
            r.game_slug,
            r.discipline,
            r.athlete_name,
            a.medals_count,
            a.gold_medals,
            a.silver_medals, 
            a.bronze_medals
        FROM olympic_results r
        LEFT JOIN olympic_athletes a ON r.athlete_name = a.full_name
        WHERE r.medal_type IN ('GOLD', 'SILVER', 'BRONZE')
        """
        
        self.historical_data = self.db.execute_query(historical_query)
        
        # Donnees scrapees 2024
        scraped_query = """
        SELECT name, country, sport, source, qualified_2024, type
        FROM scraped_athletes_2024
        WHERE qualified_2024 = true
        """
        
        self.scraped_data = self.db.execute_query(scraped_query)
        
        print(f"Donnees historiques: {len(self.historical_data)} medailles")
        print(f"Donnees 2024: {len(self.scraped_data)} athletes qualifies")
        
    def analyze_france_patterns(self):
        """Analyse les patterns de medailles de la France"""
        if self.historical_data is None:
            self.load_data()
            
        print("\\n=== ANALYSE PATTERNS FRANCE ===")
        
        # Medailles France par JO
        france_data = self.historical_data[
            self.historical_data['country_name'] == 'France'
        ].copy()
        
        # Extraire l'annee du game_slug
        france_data['year'] = france_data['game_slug'].str.extract(r'(\\d{4})')
        france_data['year'] = pd.to_numeric(france_data['year'], errors='coerce')
        
        # Medailles par annee et type
        medals_by_year = france_data.groupby(['year', 'medal_type']).size().unstack(fill_value=0)
        
        # Calculer tendances recentes (derniers 30 ans)
        recent_years = medals_by_year[medals_by_year.index >= 1992]
        
        print(f"Medailles France total: {len(france_data)}")
        
        # Verifier les colonnes disponibles
        available_medals = medals_by_year.columns.tolist()
        print(f"Types de medailles disponibles: {available_medals}")
        
        # Calculs securises
        gold_avg = recent_years['GOLD'].mean() if 'GOLD' in available_medals else 0
        silver_avg = recent_years['SILVER'].mean() if 'SILVER' in available_medals else 0
        bronze_avg = recent_years['BRONZE'].mean() if 'BRONZE' in available_medals else 0
        
        print(f"Moyenne Or par JO (1992-2020): {gold_avg:.1f}")
        print(f"Moyenne Argent par JO (1992-2020): {silver_avg:.1f}")
        print(f"Moyenne Bronze par JO (1992-2020): {bronze_avg:.1f}")
        
        # Progression recente
        last_3_olympics = recent_years.tail(3)
        print("\\nTendance 3 derniers JO:")
        for year in last_3_olympics.index:
            total = last_3_olympics.loc[year].sum()
            print(f"  {int(year)}: {total} medailles total")
            
        # Athletes francais 2024
        france_2024 = self.scraped_data[
            self.scraped_data['country'] == 'France'
        ]
        print(f"\\nAthletes francais qualifies 2024: {len(france_2024)}")
        
        return {
            'historical_medals': len(france_data),
            'avg_gold_recent': gold_avg,
            'avg_silver_recent': silver_avg, 
            'avg_bronze_recent': bronze_avg,
            'athletes_2024': len(france_2024),
            'recent_trend': last_3_olympics.sum(axis=1).tolist() if not last_3_olympics.empty else []
        }
    
    def analyze_top_countries_patterns(self):
        """Analyse les patterns des top pays"""
        if self.historical_data is None:
            self.load_data()
            
        print("\\n=== ANALYSE TOP 25 PAYS ===")
        
        # Top pays par total medailles
        country_totals = self.historical_data.groupby('country_name').size().sort_values(ascending=False)
        top_25 = country_totals.head(25)
        
        print("Top 10 pays historiques:")
        for i, (country, total) in enumerate(top_25.head(10).items(), 1):
            print(f"  {i:2d}. {country}: {total} medailles")
        
        # Analyse par type de medaille pour top 25
        top_countries_detail = self.historical_data[
            self.historical_data['country_name'].isin(top_25.index)
        ].groupby(['country_name', 'medal_type']).size().unstack(fill_value=0)
        
        # Calculer ratios or/argent/bronze
        top_countries_detail['total'] = top_countries_detail.sum(axis=1)
        top_countries_detail['gold_ratio'] = top_countries_detail['GOLD'] / top_countries_detail['total']
        
        print(f"\\nPays avec meilleur ratio d'or:")
        gold_leaders = top_countries_detail.sort_values('gold_ratio', ascending=False).head(5)
        for country in gold_leaders.index:
            ratio = gold_leaders.loc[country, 'gold_ratio']
            total = gold_leaders.loc[country, 'total']
            print(f"  {country}: {ratio:.2%} d'or ({total} medailles total)")
            
        return {
            'top_25_countries': top_25.to_dict(),
            'medals_breakdown': top_countries_detail.to_dict(),
            'gold_leaders': gold_leaders.head(10).to_dict()
        }
    
    def analyze_individual_athletes_patterns(self):
        """Analyse patterns pour predictions individuelles"""
        if self.historical_data is None:
            self.load_data()
            
        print("\\n=== ANALYSE ATHLETES INDIVIDUELS ===")
        
        # Athletes historiques avec medailles
        medaled_athletes = self.historical_data.dropna(subset=['athlete_name'])
        athlete_stats = medaled_athletes.groupby('athlete_name').agg({
            'medal_type': 'count',
            'country_name': 'first',
            'discipline': lambda x: list(x.unique())
        }).rename(columns={'medal_type': 'total_medals'})
        
        # Top athletes historiques
        top_athletes = athlete_stats.sort_values('total_medals', ascending=False).head(20)
        
        print("Top 10 athletes historiques:")
        for i, (athlete, data) in enumerate(top_athletes.head(10).iterrows(), 1):
            country = data['country_name']
            medals = data['total_medals']
            sports = ', '.join(data['discipline'][:2])  # Max 2 sports
            print(f"  {i:2d}. {athlete} ({country}): {medals} medailles - {sports}")
        
        # Analyse par sport pour athletes 2024
        sports_2024 = self.scraped_data['sport'].value_counts()
        print(f"\\nSports les plus representes en 2024:")
        for sport, count in sports_2024.head(8).items():
            if sport and sport != 'nan':
                print(f"  - {sport}: {count} athletes")
        
        # Pays avec plus d'athletes qualifies 2024
        countries_2024 = self.scraped_data['country'].value_counts()
        print(f"\\nPays avec plus d'athletes qualifies 2024:")
        for country, count in countries_2024.head(8).items():
            if country and country != 'nan':
                historical_medals = len(self.historical_data[
                    self.historical_data['country_name'] == country
                ])
                print(f"  - {country}: {count} athletes ({historical_medals} medailles historiques)")
        
        return {
            'top_athletes_historical': top_athletes.head(50).to_dict(),
            'sports_representation_2024': sports_2024.to_dict(),
            'countries_2024_vs_historical': {
                country: {
                    'athletes_2024': count,
                    'historical_medals': len(self.historical_data[
                        self.historical_data['country_name'] == country
                    ])
                }
                for country, count in countries_2024.head(15).items()
                if country and country != 'nan'
            }
        }
    
    def generate_prediction_features(self):
        """Genere les features pour les modeles predictifs"""
        if self.historical_data is None:
            self.load_data()
            
        print("\\n=== GENERATION FEATURES PREDICTIVES ===")
        
        # Features France
        france_features = self.analyze_france_patterns()
        
        # Features top pays
        countries_features = self.analyze_top_countries_patterns()
        
        # Features athletes individuels
        athletes_features = self.analyze_individual_athletes_patterns()
        
        # Features contextuelles Paris 2024
        paris_features = {
            'host_country': 'France',
            'total_athletes_qualified': len(self.scraped_data),
            'total_sports': self.scraped_data['sport'].nunique(),
            'countries_participating': self.scraped_data['country'].nunique()
        }
        
        print(f"\\nFeatures contextuelles Paris 2024:")
        print(f"  - Pays hote: {paris_features['host_country']}")
        print(f"  - Athletes qualifies identifies: {paris_features['total_athletes_qualified']}")
        print(f"  - Sports representes: {paris_features['total_sports']}")
        print(f"  - Pays participants: {paris_features['countries_participating']}")
        
        return {
            'france': france_features,
            'countries': countries_features, 
            'athletes': athletes_features,
            'paris_2024': paris_features
        }
    
    def run_full_analysis(self):
        """Execute l'analyse complete"""
        print("=== ANALYSE COMPLETE DONNEES OLYMPIQUES ===")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print()
        
        if not self.db.test_connection():
            print("ERREUR: Impossible de se connecter a la base de donnees")
            return None
        
        try:
            # Charger donnees
            self.load_data()
            
            # Generer toutes les features
            features = self.generate_prediction_features()
            
            print("\\n=== ANALYSE TERMINEE ===")
            print("Features generees pour 3 modeles predictifs:")
            print("  1. Predictions medailles France")
            print("  2. Predictions Top 25 pays") 
            print("  3. Predictions athletes individuels")
            
            return features
            
        except Exception as e:
            print(f"ERREUR lors de l'analyse: {e}")
            return None

if __name__ == "__main__":
    analyzer = OlympicsDataAnalyzer()
    results = analyzer.run_full_analysis()
    
    if results:
        print("\\nAnalyse reussie - Donnees pretes pour modelisation IA")
    else:
        print("\\nEchec de l'analyse")