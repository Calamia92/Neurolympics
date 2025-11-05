#!/usr/bin/env python3
"""
Script de test pour la webapp Neurolympics
Vérifie que tout fonctionne avant le lancement complet
"""

import sys
import os

# Ajouter le répertoire parent au PATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test des imports principaux"""
    print("Test des imports...")
    
    try:
        from flask import Flask
        print("[OK] Flask OK")
    except ImportError as e:
        print(f"[ERREUR] Flask manquant: {e}")
        return False
    
    try:
        import pandas as pd
        print("[OK] Pandas OK")
    except ImportError as e:
        print(f"[ERREUR] Pandas manquant: {e}")
        return False
    
    try:
        import plotly.express as px
        print("[OK] Plotly OK")
    except ImportError as e:
        print(f"[ERREUR] Plotly manquant: {e}")
        return False
    
    try:
        from src.database.connection import get_db_connection
        print("[OK] Database connection OK")
    except ImportError as e:
        print(f"[ERREUR] Database connection manquant: {e}")
        return False
    
    try:
        from models.random_forest.olympics_ai_predictor_v2 import OlympicsAIPredictorV2
        print("[OK] Modèle IA V2 OK")
    except ImportError as e:
        print(f"[ERREUR] Modèle IA V2 manquant: {e}")
        return False
    
    return True

def test_database():
    """Test de la connexion base de donnees"""
    print("\n Test de la base de donnees...")
    
    try:
        from src.database.connection import get_db_connection
        db = get_db_connection()
        
        if db.test_connection():
            print("[OK] Connexion PostgreSQL OK")
            
            # Test quelques requêtes simples
            try:
                result = db.execute_query("SELECT COUNT(*) as count FROM paris2024_athletes")
                athletes_count = result.iloc[0]['count']
                print(f"[OK] Table paris2024_athletes: {athletes_count} athlètes")
                
                result = db.execute_query("SELECT COUNT(DISTINCT country) as count FROM paris2024_athletes")
                countries_count = result.iloc[0]['count']
                print(f"[OK] Pays participants: {countries_count}")
                
                return True
                
            except Exception as e:
                print(f"[ERREUR] Erreur requête SQL: {e}")
                return False
        else:
            print("[ERREUR] Connexion PostgreSQL échouée")
            return False
            
    except Exception as e:
        print(f"[ERREUR] Erreur connexion DB: {e}")
        return False

def test_model():
    """Test du modèle IA"""
    print("\n Test du modèle IA V2...")
    
    try:
        from models.random_forest.olympics_ai_predictor_v2 import OlympicsAIPredictorV2
        
        predictor = OlympicsAIPredictorV2()
        print("[OK] Modèle IA V2 instancié")
        
        # Vérifier si le modèle pré-entraîné existe
        model_path = "models/trained/random_forest_model_v2.pkl"
        
        if os.path.exists(model_path):
            print("[OK] Modèle pré-entraîné trouvé")
            
            try:
                predictor.load_models(model_path)
                print("[OK] Modèle chargé avec succès")
                return True
            except Exception as e:
                print(f"[ERREUR] Erreur chargement modèle: {e}")
                return False
        else:
            print("[ATTENTION] Modèle pré-entraîné non trouvé - entraînement nécessaire")
            return True  # Pas bloquant, l'app peut s'entraîner
            
    except Exception as e:
        print(f"[ERREUR] Erreur modèle IA: {e}")
        return False

def test_templates():
    """Test des templates HTML"""
    print("\n Test des templates...")
    
    templates_dir = "templates"
    required_templates = [
        "base.html",
        "index.html", 
        "data.html",
        "predictions.html",
        "visualizations.html",
        "analysis.html"
    ]
    
    missing_templates = []
    
    for template in required_templates:
        template_path = os.path.join(templates_dir, template)
        if os.path.exists(template_path):
            print(f"[OK] {template}")
        else:
            print(f"[ERREUR] {template} manquant")
            missing_templates.append(template)
    
    return len(missing_templates) == 0

def test_flask_app():
    """Test de l'application Flask"""
    print("\n Test de l'application Flask...")
    
    try:
        from app import app
        
        # Tester la configuration
        assert app.config['SECRET_KEY'] is not None
        print("[OK] Configuration Flask OK")
        
        # Tester le contexte d'application
        with app.app_context():
            print("[OK] Contexte d'application OK")
        
        # Tester les routes principales
        with app.test_client() as client:
            
            # Test route d'accueil (sans initialisation complète)
            try:
                from app import init_app
                print("[OK] Fonction init_app importée")
            except Exception as e:
                print(f"[ATTENTION] Init_app: {e}")
        
        return True
        
    except Exception as e:
        print(f"[ERREUR] Erreur Flask: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("Test de la WebApp Neurolympics")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Base de donnees", test_database),
        ("Modèle IA", test_model),
        ("Templates", test_templates),
        ("Application Flask", test_flask_app)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERREUR] Erreur critique dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("RESUME DES TESTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "[OK] PASSE" if result else "[ERREUR] ECHEC"
        print(f"{test_name:<20} : {status}")
        if result:
            passed += 1
    
    print(f"\nScore: {passed}/{total} tests reussis")
    
    if passed == total:
        print("SUCCES: Tous les tests sont passes! L'application est prete.")
        print("\nLANCEMENT: Pour lancer l'application:")
        print("   python run.py")
        return True
    else:
        print("[ATTENTION] Certains tests ont echoue. Verifiez les erreurs ci-dessus.")
        print("\nCONSEIL: Actions recommandees:")
        
        if not results[0][1]:  # Imports
            print("   - Installez les dépendances: pip install -r requirements.txt")
        if not results[1][1]:  # Database
            print("   - Vérifiez la configuration PostgreSQL")
        if not results[2][1]:  # Modèle
            print("   - Entraînez le modèle V2 ou vérifiez le chemin")
        if not results[3][1]:  # Templates
            print("   - Vérifiez que tous les templates sont présents")
        if not results[4][1]:  # Flask
            print("   - Vérifiez la configuration Flask")
        
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)