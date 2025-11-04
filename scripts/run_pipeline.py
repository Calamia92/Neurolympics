#!/usr/bin/env python3
"""
Script principal pour exécuter le pipeline d'intégration des données olympiques
Point d'entrée unique pour lancer l'ensemble du processus
"""

import sys
import os

# Ajouter le dossier racine du projet au path Python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.pipeline.integration import main as run_integration_pipeline

def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("        NEUROLYMPICS - PIPELINE D'INTEGRATION")
    print("=" * 60)
    print(f"Dossier de travail: {os.getcwd()}")
    print(f"Dossier du projet: {project_root}")
    print()
    
    try:
        # Changer le repertoire de travail vers la racine du projet
        os.chdir(project_root)
        print(f"Bascule vers: {os.getcwd()}")
        
        # Lancer le pipeline principal
        run_integration_pipeline()
        
    except Exception as e:
        print(f"ERREUR: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)