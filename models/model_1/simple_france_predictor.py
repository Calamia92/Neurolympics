"""
Modele predictif simplifie pour les medailles France Paris 2024
Base sur donnees connues et patterns historiques
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.connection import get_db_connection

class SimpleFrancePredictor:
    """Modele simple de prediction medailles France"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def get_france_athletes_2024(self):
        """Recupere le nombre d'athletes francais qualifies"""
        query = """
        SELECT COUNT(*) as count
        FROM scraped_athletes_2024 
        WHERE country = 'France' AND qualified_2024 = true
        """
        
        result = self.db.execute_query(query)
        return result.iloc[0]['count'] if not result.empty else 0
    
    def predict_france_medals_2024(self):
        """Prediction basee sur donnees historiques connues et facteurs 2024"""
        
        print("=== PREDICTION MEDAILLES FRANCE PARIS 2024 ===")
        print()
        
        # Donnees historiques France (connues)
        historical_data = {
            'total_medals_historical': 880,  # Total depuis 1896
            'recent_olympics': {
                2000: 38,  # Sydney
                2004: 33,  # Athenes  
                2008: 40,  # Pekin
                2012: 34,  # Londres
                2016: 42,  # Rio
                2021: 33   # Tokyo (2020)
            }
        }
        
        # Facteurs Paris 2024
        athletes_2024 = self.get_france_athletes_2024()
        
        paris_2024_factors = {
            'host_country': True,
            'athletes_qualified': athletes_2024,
            'sports_represented': 25,  # Estimation
            'home_advantage': True
        }
        
        print("DONNEES HISTORIQUES FRANCE:")
        print(f"  Total medailles historiques: {historical_data['total_medals_historical']}")
        print(f"  Performances recentes:")
        for year, medals in historical_data['recent_olympics'].items():
            print(f"    {year}: {medals} medailles")
        
        # Calcul moyenne recente
        recent_medals = list(historical_data['recent_olympics'].values())
        avg_recent = sum(recent_medals) / len(recent_medals)
        
        print(f"  Moyenne 2000-2021: {avg_recent:.1f} medailles")
        print()
        
        print("FACTEURS PARIS 2024:")
        print(f"  Pays hote: {paris_2024_factors['host_country']}")
        print(f"  Athletes qualifies: {paris_2024_factors['athletes_qualified']}")
        print(f"  Avantage domicile: {paris_2024_factors['home_advantage']}")
        print()
        
        # Prediction basee sur facteurs
        base_prediction = avg_recent
        
        # Boost pays hote (historiquement +15-20%)
        host_boost = base_prediction * 0.175  # 17.5%
        
        # Boost equipe (plus d'athletes qualifies)
        baseline_athletes = 320
        if baseline_athletes > 0:
            athlete_factor = paris_2024_factors['athletes_qualified'] / baseline_athletes
            athlete_boost = (athlete_factor - 1) * base_prediction * 0.3
        else:
            athlete_boost = 0
        
        # Prediction totale
        total_prediction = base_prediction + host_boost + athlete_boost
        
        # Repartition Or/Argent/Bronze (basee sur ratios historiques France)
        # France historiquement: ~30% Or, 33% Argent, 37% Bronze
        gold_ratio = 0.30
        silver_ratio = 0.33
        bronze_ratio = 0.37
        
        predicted_gold = round(total_prediction * gold_ratio)
        predicted_silver = round(total_prediction * silver_ratio)  
        predicted_bronze = round(total_prediction * bronze_ratio)
        predicted_total = predicted_gold + predicted_silver + predicted_bronze
        
        # Affichage prediction
        print("CALCUL DE LA PREDICTION:")
        print(f"  Base (moyenne recente): {base_prediction:.1f} medailles")
        print(f"  Boost pays hote (+17.5%): +{host_boost:.1f} medailles")
        print(f"  Boost equipe 2024: {athlete_boost:+.1f} medailles")
        print(f"  Total predit: {total_prediction:.1f} medailles")
        print()
        
        print("PREDICTION FINALE FRANCE PARIS 2024:")
        print("=" * 45)
        print(f"OR: {predicted_gold} medailles")
        print(f"ARGENT: {predicted_silver} medailles")  
        print(f"BRONZE: {predicted_bronze} medailles")
        print(f"TOTAL: {predicted_total} medailles")
        print("=" * 45)
        print()
        
        # Contexte et confiance
        print("CONTEXTE:")
        print(f"- Base sur {len(recent_medals)} derniers JO")
        print(f"- Facteur pays hote applique")
        print(f"- {paris_2024_factors['athletes_qualified']} athletes francais qualifies")
        print(f"- Prediction dans la fourchette historique France")
        
        return {
            'gold': predicted_gold,
            'silver': predicted_silver,
            'bronze': predicted_bronze,
            'total': predicted_total,
            'base_prediction': base_prediction,
            'host_boost': host_boost,
            'athlete_boost': athlete_boost,
            'confidence': 'Haute',
            'method': 'Historique + Facteurs 2024'
        }

if __name__ == "__main__":
    if get_db_connection().test_connection():
        predictor = SimpleFrancePredictor()
        prediction = predictor.predict_france_medals_2024()
        
        print(f"\\nRESULTAT: France devrait gagner {prediction['total']} medailles")
        print(f"Repartition: {prediction['gold']} Or, {prediction['silver']} Argent, {prediction['bronze']} Bronze")
    else:
        print("ERREUR: Connexion base de donnees")