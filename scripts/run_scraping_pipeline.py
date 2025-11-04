#!/usr/bin/env python3
"""
Pipeline automatique de scraping pour enrichir les donnees JO 2024
Point d'entree principal pour lancer le scraping et l'integration
"""

import sys
import os

# Ajouter le dossier racine du projet au path Python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.scraping.scrapers.paris2024_scraper import Paris2024Scraper
from src.scraping.scrapers.olympics_scraper import OlympicsScraper
from src.scraping.scrapers.wikipedia_scraper import WikipediaScraper
from src.scraping.scrapers.athletes_2024_scraper import Athletes2024Scraper
from src.scraping.scrapers.team_athletes_scraper import TeamAthletesScraper
from src.scraping.scrapers.wikipedia_teams_scraper import WikipediaTeamsScraper
from src.scraping.db_integration import ScrapingDBIntegrator
import argparse
from datetime import datetime

def run_scraper(scraper_name, integrator):
    """Execute un scraper specifique"""
    
    scrapers = {
        'paris2024': Paris2024Scraper,
        'olympics': OlympicsScraper,
        'wikipedia': WikipediaScraper,
        'athletes2024': Athletes2024Scraper,
        'teamathletes': TeamAthletesScraper,
        'wikipediateams': WikipediaTeamsScraper,
    }
    
    if scraper_name not in scrapers:
        print(f"ERREUR: Scraper '{scraper_name}' non reconnu")
        print(f"Scrapers disponibles: {list(scrapers.keys())}")
        return False
    
    print(f"=== EXECUTION SCRAPER: {scraper_name.upper()} ===")
    start_time = datetime.now()
    
    try:
        # Initialiser le scraper
        scraper_class = scrapers[scraper_name]
        scraper = scraper_class()
        
        # Executer le scraping
        print("1. Scraping en cours...")
        data = scraper.run()
        
        if data is None or data.empty:
            print(f"ERREUR: Aucune donnee extraite par {scraper_name}")
            return False
        
        print(f"   OK: {len(data)} enregistrements extraits")
        
        # Integration en base de donnees
        print("2. Integration en base...")
        success = integrator.integrate_scraped_athletes(scraper_name)
        
        if success:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"   OK: Integration reussie en {duration:.1f}s")
            return True
        else:
            print("   ERREUR: Echec integration")
            return False
            
    except Exception as e:
        print(f"ERREUR scraper {scraper_name}: {e}")
        return False

def run_all_scrapers(integrator):
    """Execute tous les scrapers disponibles"""
    
    scrapers_to_run = ['wikipedia', 'athletes2024', 'olympics', 'paris2024']  # Ordre de priorite
    results = {}
    
    print("=== EXECUTION DE TOUS LES SCRAPERS ===")
    print()
    
    for scraper_name in scrapers_to_run:
        print(f"Execution du scraper: {scraper_name}")
        results[scraper_name] = run_scraper(scraper_name, integrator)
        print()
    
    # Rapport final
    print("=== RAPPORT FINAL ===")
    successful_scrapers = [name for name, success in results.items() if success]
    failed_scrapers = [name for name, success in results.items() if not success]
    
    print(f"Scrapers reussis: {len(successful_scrapers)}/{len(scrapers_to_run)}")
    if successful_scrapers:
        print(f"  Succes: {', '.join(successful_scrapers)}")
    if failed_scrapers:
        print(f"  Echecs: {', '.join(failed_scrapers)}")
    
    return len(successful_scrapers) > 0

def show_current_data(integrator):
    """Affiche les donnees actuellement en base"""
    
    print("=== DONNEES ACTUELLES ===")
    print()
    
    try:
        stats = integrator.get_scraped_athletes_stats()
        
        if stats['total_athletes'] is not None:
            total = stats['total_athletes'].iloc[0]['count']
            print(f"Total athletes scrapes: {total}")
        
        if stats['qualified_count'] is not None:
            qualified = stats['qualified_count'].iloc[0]['count']
            print(f"Athletes qualifies 2024: {qualified}")
        
        print()
        print("Par source:")
        if stats['by_source'] is not None and not stats['by_source'].empty:
            for _, row in stats['by_source'].iterrows():
                print(f"  - {row['source']}: {row['count']} athletes")
        
        print()
        print("Top 10 pays:")
        if stats['by_country'] is not None and not stats['by_country'].empty:
            for _, row in stats['by_country'].head(10).iterrows():
                print(f"  - {row['country']}: {row['count']} athletes")
        
        print()
        print("Historique recent:")
        if stats['recent_scraping'] is not None and not stats['recent_scraping'].empty:
            for _, row in stats['recent_scraping'].iterrows():
                status_icon = "OK" if row['status'] == 'SUCCESS' else "ERREUR"
                print(f"  {status_icon} {row['scraper_name']}: {row['records_count']} records ({row['completed_at']})")
        
    except Exception as e:
        print(f"ERREUR affichage donnees: {e}")

def main():
    """Fonction principale"""
    
    parser = argparse.ArgumentParser(description='Pipeline de scraping olympique')
    parser.add_argument('--scraper', '-s', 
                       choices=['paris2024', 'olympics', 'wikipedia', 'athletes2024', 'teamathletes', 'wikipediateams', 'all'], 
                       default='all',
                       help='Scraper a executer (par defaut: tous)')
    parser.add_argument('--show-data', '-d', 
                       action='store_true',
                       help='Afficher les donnees actuelles')
    parser.add_argument('--setup', 
                       action='store_true',
                       help='Initialiser les tables de scraping')
    
    args = parser.parse_args()
    
    print("PIPELINE DE SCRAPING OLYMPIQUE")
    print("=" * 50)
    print(f"Dossier de travail: {os.getcwd()}")
    print(f"Dossier du projet: {project_root}")
    print()
    
    # Changer vers le dossier du projet
    os.chdir(project_root)
    
    # Initialiser l'integrateur
    integrator = ScrapingDBIntegrator()
    
    # Tester la connexion
    if not integrator.db_conn.test_connection():
        print("ERREUR: Impossible de se connecter a la base de donnees")
        return 1
    
    # Setup des tables si demande
    if args.setup:
        print("Initialisation des tables...")
        if integrator.create_scraped_tables():
            print("OK: Tables initialisees")
        else:
            print("ERREUR: Echec initialisation tables")
            return 1
    
    # Affichage des donnees si demande
    if args.show_data:
        show_current_data(integrator)
        return 0
    
    # Execution des scrapers
    success = False
    
    if args.scraper == 'all':
        success = run_all_scrapers(integrator)
    else:
        success = run_scraper(args.scraper, integrator)
    
    if success:
        print()
        print("PIPELINE TERMINE AVEC SUCCES!")
        print("Utilisez --show-data pour voir les donnees extraites")
        return 0
    else:
        print()
        print("PIPELINE TERMINE AVEC ERREURS")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)