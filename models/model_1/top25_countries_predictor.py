"""
Modele predictif pour le classement des 25 premiers pays aux JO Paris 2024
Base sur donnees historiques et tendances recentes
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.connection import get_db_connection
import pandas as pd

class Top25CountriesPredictor:
    """Modele de prediction du classement top 25 pays"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def get_historical_top_countries(self):
        """Recupere le classement historique des pays"""
        query = """
        SELECT 
            country_name,
            COUNT(*) as total_medals,
            SUM(CASE WHEN medal_type = 'GOLD' THEN 1 ELSE 0 END) as gold_medals,
            SUM(CASE WHEN medal_type = 'SILVER' THEN 1 ELSE 0 END) as silver_medals,
            SUM(CASE WHEN medal_type = 'BRONZE' THEN 1 ELSE 0 END) as bronze_medals
        FROM olympic_results 
        WHERE medal_type IN ('GOLD', 'SILVER', 'BRONZE')
        GROUP BY country_name 
        ORDER BY total_medals DESC
        LIMIT 30
        """
        
        result = self.db.execute_query(query)
        return result
    
    def get_countries_2024_athletes(self):
        """Recupere le nombre d'athletes par pays pour 2024"""
        query = """
        SELECT 
            country,
            COUNT(*) as athletes_2024
        FROM paris2024_athletes 
        WHERE sport != 'Unknown' AND country != ''
        GROUP BY country 
        ORDER BY athletes_2024 DESC
        """
        
        result = self.db.execute_query(query)
        return result
    
    def predict_top25_countries_2024(self):
        """Prediction du top 25 des pays pour Paris 2024"""
        
        print("=== PREDICTION TOP 25 PAYS PARIS 2024 ===")
        print()
        
        # Donnees historiques
        historical = self.get_historical_top_countries()
        
        # Athletes 2024
        athletes_2024 = self.get_countries_2024_athletes()
        
        print("TOP 15 PAYS HISTORIQUES:")
        for i, (_, row) in enumerate(historical.head(15).iterrows(), 1):
            country = row['country_name']
            total = row['total_medals']
            gold = row['gold_medals']
            print(f"  {i:2d}. {country}: {total} medailles ({gold} or)")
        
        print()
        print("TOP 10 PAYS PAR ATHLETES 2024:")
        for i, (_, row) in enumerate(athletes_2024.head(10).iterrows(), 1):
            country = row['country']
            athletes = row['athletes_2024']
            print(f"  {i:2d}. {country}: {athletes} athletes")
        
        # Pays a exclure (n'existent plus ou ont change de nom)
        excluded_countries = {
            'Soviet Union', 
            'German Democratic Republic (Germany)',
            'Yugoslavia',
            'Czechoslovakia',
            'East Germany',
            'West Germany'
        }
        
        # Fusion donnees historiques et 2024
        merged_data = []
        
        for _, hist_row in historical.iterrows():
            country = hist_row['country_name']
            
            # Exclure pays inexistants
            if country in excluded_countries:
                continue
            
            # Chercher athletes 2024 pour ce pays
            athletes_row = athletes_2024[athletes_2024['country'] == country]
            athletes_count = athletes_row.iloc[0]['athletes_2024'] if not athletes_row.empty else 0
            
            # Calcul score predictif
            historical_score = hist_row['total_medals']
            recent_boost = athletes_count * 0.5  # Facteur athletes 2024
            
            # Ajustements speciaux
            country_adjustments = {
                'France': 1.2,  # Pays hote
                'United States of America': 1.1,  # Puissance sportive
                'People\'s Republic of China': 1.05,  # Investissement continu
                'Great Britain': 0.95,  # Post-Londres decline
                'Germany': 1.0,
                'Italy': 1.0,
                'Australia': 1.0,
                'Japan': 0.9,  # Post-Tokyo
                'Netherlands': 1.0,
                'Spain': 1.0
            }
            
            adjustment = country_adjustments.get(country, 1.0)
            
            predicted_total = (historical_score * 0.3 + recent_boost) * adjustment
            
            # Estimation repartition medailles
            gold_ratio = hist_row['gold_medals'] / hist_row['total_medals'] if hist_row['total_medals'] > 0 else 0.33
            
            predicted_gold = round(predicted_total * gold_ratio)
            predicted_silver = round(predicted_total * 0.33)
            predicted_bronze = round(predicted_total * 0.34)
            predicted_medals = predicted_gold + predicted_silver + predicted_bronze
            
            merged_data.append({
                'country': country,
                'historical_total': hist_row['total_medals'],
                'historical_gold': hist_row['gold_medals'],
                'athletes_2024': athletes_count,
                'predicted_total': predicted_medals,
                'predicted_gold': predicted_gold,
                'predicted_silver': predicted_silver,
                'predicted_bronze': predicted_bronze,
                'adjustment_factor': adjustment
            })
        
        # Trier par prediction
        merged_data.sort(key=lambda x: x['predicted_total'], reverse=True)
        
        print()
        print("PREDICTION TOP 25 PAYS PARIS 2024:")
        print("=" * 80)
        print(f"{'#':<3} {'PAYS':<25} {'TOTAL':<6} {'OR':<4} {'ARG':<4} {'BRO':<4} {'ATH 2024':<8}")
        print("-" * 80)
        
        top_25_predictions = []
        
        for i, data in enumerate(merged_data[:25], 1):
            country = data['country']
            if len(country) > 24:
                country = country[:21] + "..."
            
            total = data['predicted_total']
            gold = data['predicted_gold']
            silver = data['predicted_silver']
            bronze = data['predicted_bronze']
            athletes = data['athletes_2024']
            
            print(f"{i:<3} {country:<25} {total:<6} {gold:<4} {silver:<4} {bronze:<4} {athletes:<8}")
            
            top_25_predictions.append({
                'rank': i,
                'country': data['country'],
                'predicted_total': total,
                'predicted_gold': gold,
                'predicted_silver': silver,
                'predicted_bronze': bronze,
                'athletes_2024': athletes
            })
        
        print("-" * 80)
        print()
        
        # Statistiques globales
        total_medals_predicted = sum(d['predicted_total'] for d in merged_data[:25])
        total_gold_predicted = sum(d['predicted_gold'] for d in merged_data[:25])
        
        print("STATISTIQUES GLOBALES TOP 25:")
        print(f"  Total medailles predites: {total_medals_predicted}")
        print(f"  Total medailles d'or predites: {total_gold_predicted}")
        print()
        
        # Top 5 resume
        print("RESUME TOP 5:")
        for i, country_data in enumerate(top_25_predictions[:5], 1):
            country = country_data['country']
            total = country_data['predicted_total']
            gold = country_data['predicted_gold']
            print(f"  {i}. {country}: {total} medailles ({gold} or)")
        
        return {
            'top_25_predictions': top_25_predictions,
            'total_medals_predicted': total_medals_predicted,
            'methodology': 'Historique + Athletes 2024 + Ajustements',
            'confidence': 'Moyenne-Haute'
        }

if __name__ == "__main__":
    if get_db_connection().test_connection():
        predictor = Top25CountriesPredictor()
        results = predictor.predict_top25_countries_2024()
        
        print()
        print(f"PREDICTION TERMINEE!")
        print(f"Top 5 predit: {', '.join([p['country'] for p in results['top_25_predictions'][:5]])}")
    else:
        print("ERREUR: Connexion base de donnees")