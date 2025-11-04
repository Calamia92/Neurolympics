"""
Modèle 3 - Prédiction top 25 pays
TODO: Implémentez votre approche IA ici
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.connection import get_db_connection

class Model3CountriesPredictor:
    """
    Placeholder pour votre modèle de classement pays
    
    TODO pour votre équipe:
    1. Analyser les données historiques par pays
    2. Choisir votre approche IA (ML, DL, stats, etc.)
    3. Entraîner votre modèle
    4. Implémenter la méthode predict_top25_countries()
    """
    
    def __init__(self):
        self.db = get_db_connection()
        # TODO: Initialisez votre modèle ici
        pass
    
    def train_model(self):
        """TODO: Implémentez l'entraînement de votre modèle"""
        pass
    
    def predict_top25_countries(self):
        """
        TODO: Implémentez votre prédiction pour le top 25 des pays
        
        Retour attendu:
        {
            'top_25_predictions': [
                {
                    'rank': int,
                    'country': str,
                    'predicted_total': int,
                    'predicted_gold': int,
                    'predicted_silver': int,
                    'predicted_bronze': int
                }, ...
            ],
            'approach': str,
            'confidence': str
        }
        """
        
        # PLACEHOLDER - Remplacez par votre logique
        placeholder_countries = []
        for i in range(25):
            placeholder_countries.append({
                'rank': i + 1,
                'country': f'TODO_Country_{i+1}',
                'predicted_total': 0,
                'predicted_gold': 0,
                'predicted_silver': 0,
                'predicted_bronze': 0
            })
        
        return {
            'top_25_predictions': placeholder_countries,
            'approach': 'TODO: Votre approche IA',
            'confidence': 'TODO'
        }

if __name__ == "__main__":
    # Test de votre modèle
    predictor = Model3CountriesPredictor()
    result = predictor.predict_top25_countries()
    print(f"Modèle 3 - Countries: Top 3 = {[p['country'] for p in result['top_25_predictions'][:3]]}")