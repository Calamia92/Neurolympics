"""
Modele predictif pour les medailles de la France aux JO Paris 2024
Utilise les patterns historiques et l'effet pays hote
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.connection import get_db_connection
import pandas as pd
import numpy as np
from datetime import datetime
import re

class FranceMedalsPredictor:
    """Modele de prediction des medailles francaises Paris 2024"""
    
    def __init__(self):
        self.db = get_db_connection()
        self.historical_data = None
        self.predictions = None
        
    def load_france_historical_data(self):
        """Charge l'historique des medailles francaises"""
        print("Chargement historique medailles France...")
        
        query = """
        SELECT 
            medal_type,
            game_slug,
            discipline,
            athlete_name
        FROM olympic_results 
        WHERE country_name = 'France' 
        AND medal_type IN ('GOLD', 'SILVER', 'BRONZE')
        ORDER BY game_slug
        """
        
        self.historical_data = self.db.execute_query(query)
        print(f"Historique charge: {len(self.historical_data)} medailles francaises")
        
        return self.historical_data
    
    def extract_olympic_years(self):
        """Extrait les annees olympiques depuis game_slug"""
        if self.historical_data is None:
            self.load_france_historical_data()
        
        # Extraire annees
        self.historical_data['year'] = self.historical_data['game_slug'].str.extract(r'(\\d{4})')
        self.historical_data['year'] = pd.to_numeric(self.historical_data['year'], errors='coerce')
        
        # Filtrer annees valides (JO d'ete modernes)
        valid_years = self.historical_data[
            (self.historical_data['year'] >= 1896) & 
            (self.historical_data['year'] <= 2024) &
            (self.historical_data['year'] % 4 == 0)  # Annees olympiques
        ].copy()
        
        return valid_years
    
    def calculate_medals_by_olympics(self):
        """Calcule medailles par JO"""
        valid_data = self.extract_olympic_years()
        
        # Medailles par JO et type
        medals_by_year = valid_data.groupby(['year', 'medal_type']).size().unstack(fill_value=0)
        
        # Ajouter colonnes manquantes si necessaire
        for medal_type in ['GOLD', 'SILVER', 'BRONZE']:
            if medal_type not in medals_by_year.columns:
                medals_by_year[medal_type] = 0
        
        # Total par JO
        medals_by_year['TOTAL'] = medals_by_year[['GOLD', 'SILVER', 'BRONZE']].sum(axis=1)
        
        print("Medailles France par JO (derniers):")
        for year in sorted(medals_by_year.index)[-6:]:
            total = medals_by_year.loc[year, 'TOTAL']
            gold = medals_by_year.loc[year, 'GOLD']
            silver = medals_by_year.loc[year, 'SILVER']
            bronze = medals_by_year.loc[year, 'BRONZE']
            print(f"  {int(year)}: {total} total ({gold} Or, {silver} Argent, {bronze} Bronze)")
        
        return medals_by_year
    
    def analyze_host_country_effect(self):
        """Analyse l'effet pays hote sur les performances francaises"""
        
        # JO organises en France
        france_hosted = [1900, 1924, 1968, 1992]  # Paris 1900, Paris 1924, Grenoble 1968, Albertville 1992
        
        medals_by_year = self.calculate_medals_by_olympics()
        
        # Performances quand France = pays hote
        host_performances = []
        for year in france_hosted:
            if year in medals_by_year.index:
                total = medals_by_year.loc[year, 'TOTAL']
                host_performances.append(total)
                print(f"JO en France {year}: {total} medailles")
        
        # Performances moyennes hors pays hote (JO recents)
        recent_non_host = medals_by_year[
            (medals_by_year.index >= 1988) & 
            (~medals_by_year.index.isin(france_hosted))
        ]
        
        avg_non_host = recent_non_host['TOTAL'].mean() if not recent_non_host.empty else 0
        avg_host = np.mean(host_performances) if host_performances else 0
        
        host_boost = avg_host - avg_non_host if avg_non_host > 0 else 0
        
        print(f"\\nEffet pays hote analyse:")
        print(f"  Moyenne hors pays hote (1988+): {avg_non_host:.1f} medailles")
        print(f"  Moyenne en tant que pays hote: {avg_host:.1f} medailles")
        print(f"  Boost pays hote: +{host_boost:.1f} medailles")
        
        return {
            'avg_non_host': avg_non_host,
            'avg_host': avg_host,
            'host_boost': host_boost,
            'host_years': france_hosted
        }
    
    def calculate_recent_trend(self):
        """Calcule la tendance recente des performances"""
        medals_by_year = self.calculate_medals_by_olympics()
        
        # 5 derniers JO d'ete
        recent_olympics = medals_by_year[medals_by_year.index >= 2004].copy()
        
        if recent_olympics.empty:
            return {'trend': 0, 'recent_avg': 0}
        
        # Tendance lineaire simple
        years = recent_olympics.index.values
        totals = recent_olympics['TOTAL'].values
        
        if len(years) >= 2:
            # Regression lineaire simple
            trend = np.polyfit(years, totals, 1)[0]  # Pente
        else:
            trend = 0
        
        recent_avg = recent_olympics['TOTAL'].mean()
        
        print(f"\\nTendance recente (2004+):")
        print(f"  Moyenne 5 derniers JO: {recent_avg:.1f} medailles")
        print(f"  Tendance: {trend:+.2f} medailles/JO")
        
        return {
            'trend': trend,
            'recent_avg': recent_avg,
            'recent_olympics': recent_olympics.to_dict()
        }
    
    def get_athletes_2024_boost(self):
        """Calcule le boost base sur les athletes qualifies 2024"""
        
        # Athletes francais qualifies
        athletes_query = """
        SELECT COUNT(*) as count
        FROM paris2024_athletes 
        WHERE country = 'France' AND sport != 'Unknown'
        """
        
        athletes_2024 = self.db.execute_query(athletes_query)
        french_athletes = athletes_2024.iloc[0]['count'] if not athletes_2024.empty else 0
        
        # Historique taille equipe vs medailles
        medals_by_year = self.calculate_medals_by_olympics()
        recent_avg_medals = medals_by_year[medals_by_year.index >= 2000]['TOTAL'].mean()
        
        # Estimation: plus d'athletes = plus de chances
        # Baseline: ~320 athletes francais, moyennement 40 medailles
        baseline_athletes = 320
        baseline_medals = recent_avg_medals
        
        if baseline_athletes > 0:
            athlete_factor = french_athletes / baseline_athletes
            athlete_boost = (athlete_factor - 1) * baseline_medals * 0.5  # 50% de l'effet
        else:
            athlete_boost = 0
        
        print(f"\\nAnalyse equipe 2024:")
        print(f"  Athletes francais qualifies: {french_athletes}")
        print(f"  Baseline attendu: {baseline_athletes} athletes")
        print(f"  Boost equipe estime: {athlete_boost:+.1f} medailles")
        
        return {
            'french_athletes_2024': french_athletes,
            'athlete_boost': athlete_boost
        }
    
    def predict_france_medals_2024(self):
        """Prediction finale medailles France Paris 2024"""
        
        print("\\n=== PREDICTION MEDAILLES FRANCE PARIS 2024 ===")
        print()
        
        if not self.db.test_connection():
            print("ERREUR: Connexion base de donnees")
            return None
        
        # Charger donnees
        self.load_france_historical_data()
        
        # Analyses
        host_analysis = self.analyze_host_country_effect()
        trend_analysis = self.calculate_recent_trend()
        athletes_analysis = self.get_athletes_2024_boost()
        
        # Prediction de base (tendance recente)
        base_prediction = trend_analysis['recent_avg']
        
        # Ajustements
        host_boost = host_analysis['host_boost']
        trend_adjustment = trend_analysis['trend'] * 4  # 4 ans depuis dernier JO
        athlete_boost = athletes_analysis['athlete_boost']
        
        # Prediction totale
        total_predicted = base_prediction + host_boost + trend_adjustment + athlete_boost
        
        # Repartition Or/Argent/Bronze (basee sur ratios historiques)
        medals_by_year = self.calculate_medals_by_olympics()
        recent_medals = medals_by_year[medals_by_year.index >= 2000]
        
        if not recent_medals.empty:
            total_recent = recent_medals[['GOLD', 'SILVER', 'BRONZE']].sum().sum()
            gold_ratio = recent_medals['GOLD'].sum() / total_recent if total_recent > 0 else 0.33
            silver_ratio = recent_medals['SILVER'].sum() / total_recent if total_recent > 0 else 0.33
            bronze_ratio = recent_medals['BRONZE'].sum() / total_recent if total_recent > 0 else 0.34
        else:
            gold_ratio, silver_ratio, bronze_ratio = 0.33, 0.33, 0.34
        
        # Predictions finales
        predicted_gold = round(total_predicted * gold_ratio)
        predicted_silver = round(total_predicted * silver_ratio)
        predicted_bronze = round(total_predicted * bronze_ratio)
        predicted_total = predicted_gold + predicted_silver + predicted_bronze
        
        self.predictions = {
            'total': predicted_total,
            'gold': predicted_gold,
            'silver': predicted_silver,
            'bronze': predicted_bronze,
            'base_prediction': base_prediction,
            'host_boost': host_boost,
            'trend_adjustment': trend_adjustment,
            'athlete_boost': athlete_boost,
            'ratios': {
                'gold_ratio': gold_ratio,
                'silver_ratio': silver_ratio,
                'bronze_ratio': bronze_ratio
            }
        }
        
        # Affichage resultats
        print("COMPOSANTS DE LA PREDICTION:")
        print(f"  Base (moyenne recente): {base_prediction:.1f} medailles")
        print(f"  Boost pays hote: +{host_boost:.1f} medailles")
        print(f"  Ajustement tendance: {trend_adjustment:+.1f} medailles")
        print(f"  Boost equipe 2024: {athlete_boost:+.1f} medailles")
        print()
        print("PREDICTION FINALE FRANCE PARIS 2024:")
        print(f"  🥇 MEDAILLES D'OR: {predicted_gold}")
        print(f"  🥈 MEDAILLES D'ARGENT: {predicted_silver}")
        print(f"  🥉 MEDAILLES DE BRONZE: {predicted_bronze}")
        print(f"  📊 TOTAL: {predicted_total} medailles")
        
        return self.predictions

if __name__ == "__main__":
    predictor = FranceMedalsPredictor()
    results = predictor.predict_france_medals_2024()
    
    if results:
        print(f"\\nPrediction generee avec succes!")
        print(f"France devrait gagner {results['total']} medailles a Paris 2024")
    else:
        print("\\nEchec de la prediction")