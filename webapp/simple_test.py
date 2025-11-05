#!/usr/bin/env python3
"""Test simple pour webapp"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_basic():
    print("Test basique de la webapp...")
    
    # Test 1: Imports
    try:
        from flask import Flask
        print("Flask: OK")
    except:
        print("Flask: ERREUR")
        return False
    
    try:
        import pandas as pd
        print("Pandas: OK")
    except:
        print("Pandas: ERREUR")
        return False
    
    try:
        import plotly.express as px
        print("Plotly: OK")
    except:
        print("Plotly: ERREUR")
        return False
    
    # Test 2: Database
    try:
        from src.database.connection import get_db_connection
        db = get_db_connection()
        if db.test_connection():
            print("Database: OK")
        else:
            print("Database: ERREUR connexion")
            return False
    except Exception as e:
        print(f"Database: ERREUR - {e}")
        return False
    
    # Test 3: Modele
    try:
        from models.random_forest.olympics_ai_predictor_v2 import OlympicsAIPredictorV2
        print("Modele IA: OK")
    except Exception as e:
        print(f"Modele IA: ERREUR - {e}")
        return False
    
    # Test 4: Flask app
    try:
        from app import app
        print("App Flask: OK")
    except Exception as e:
        print(f"App Flask: ERREUR - {e}")
        return False
    
    print("\nTous les tests reussis!")
    return True

if __name__ == '__main__':
    success = test_basic()
    if success:
        print("\nLancement possible avec: python run.py")
    else:
        print("\nVerifiez les erreurs ci-dessus")