#!/usr/bin/env python3
"""Script de lancement simple pour webapp"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import app

def simple_init():
    """Initialisation simple"""
    try:
        # Test database
        from src.database.connection import get_db_connection
        db = get_db_connection()
        if not db.test_connection():
            print("ERREUR: Connexion database")
            return False
        
        # Test model
        from models.random_forest.olympics_ai_predictor_v2 import OlympicsAIPredictorV2
        global predictor
        predictor = OlympicsAIPredictorV2()
        
        model_path = "../models/trained/random_forest_model_v2.pkl"
        if os.path.exists(model_path):
            predictor.load_models(model_path)
            print("Modele V2 charge")
        else:
            print("Entrainement du modele...")
            predictor.train_robust_models()
            
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            predictor.save_models(model_path)
            print("Modele V2 entraine")
        
        # Injecter dans l'app
        app.predictor = predictor
        app.db = db
        
        return True
        
    except Exception as e:
        print(f"ERREUR init: {e}")
        return False

if __name__ == '__main__':
    print("Demarrage Webapp Neurolympics...")
    
    if simple_init():
        print("Application initialisee")
        print("Acces: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Echec initialisation")