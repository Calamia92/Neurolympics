#!/usr/bin/env python3
"""
Script de lancement pour la webapp Neurolympics
"""

import os
import sys

# Ajouter le répertoire parent au PATH pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import app, init_app

if __name__ == '__main__':
    print("[START] Demarrage Webapp Neurolympics...")
    
    if init_app():
        print("[OK] Application initialisée avec succès")
        print("[WEB] Accès local: http://localhost:5000")
        print("[WEB] Accès réseau: http://0.0.0.0:5000")
        print("\n[PAGES] Pages disponibles:")
        print("   - Accueil: /")
        print("   - Donnees: /data") 
        print("   - Prédictions IA: /predictions")
        print("   - Visualisations: /visualizations")
        print("   - Analyses: /analysis")
        print("\n[API] API Endpoints:")
        print("   - GET /api/data/countries")
        print("   - GET /api/data/sports")
        print("   - GET /api/search/athletes")
        print("   - GET /api/charts/*")
        
        # Configuration de développement
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            threaded=True
        )
    else:
        print("[ERREUR] Échec initialisation application")
        print("[INFO] Vérifiez:")
        print("   - Connexion base de donnees PostgreSQL")
        print("   - Fichier modèle V2: models/trained/random_forest_model_v2.pkl")
        print("   - Configuration dans src/database/connection.py")
        sys.exit(1)