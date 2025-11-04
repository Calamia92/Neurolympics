"""
Module de validation simple des données olympiques (sans emojis)
"""

import pandas as pd
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import os

class SimpleDataValidator:
    def __init__(self):
        self.datasets_path = "data/raw/"
    
    def check_all_files(self):
        """Vérifie rapidement tous les fichiers"""
        print("VERIFICATION QUALITE DES DONNEES")
        print("=" * 40)
        
        files_to_check = [
            ('olympic_athletes.json', self.check_json),
            ('olympic_hosts.xml', self.check_xml), 
            ('olympic_medals.xlsx', self.check_excel),
            ('olympic_results.html', self.check_html)
        ]
        
        results = {}
        
        for filename, check_func in files_to_check:
            filepath = os.path.join(self.datasets_path, filename)
            print(f"\nVerification: {filename}")
            print("-" * 30)
            
            try:
                result = check_func(filepath)
                results[filename] = result
                print(f"Status: {result['status']}")
                print(f"Lignes: {result.get('rows', 'N/A')}")
                if result['issues']:
                    print("Problemes detectes:")
                    for issue in result['issues'][:3]:
                        print(f"  - {issue}")
                else:
                    print("  Aucun probleme detecte")
                    
            except Exception as e:
                print(f"ERREUR: {e}")
                results[filename] = {'status': 'ERROR', 'error': str(e)}
        
        return results
    
    def check_json(self, filepath):
        """Vérifie le fichier JSON"""
        issues = []
        
        # Vérifier la taille
        file_size = os.path.getsize(filepath) / (1024*1024)
        if file_size > 30:
            issues.append(f"Fichier volumineux: {file_size:.1f}MB")
        
        # Lire un échantillon
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sample_size = min(100, len(data))
        sample = data[:sample_size]
        
        # Vérifications
        missing_names = sum(1 for item in sample if not item.get('athlete_full_name'))
        missing_urls = sum(1 for item in sample if not item.get('athlete_url'))
        
        if missing_names > 0:
            issues.append(f"{missing_names} athletes sans nom")
        
        if missing_urls > 0:
            issues.append(f"{missing_urls} athletes sans URL")
        
        status = 'WARNING' if issues else 'OK'
        
        return {
            'status': status,
            'rows': len(data),
            'issues': issues,
            'sample_checked': sample_size
        }
    
    def check_xml(self, filepath):
        """Vérifie le fichier XML"""
        issues = []
        
        tree = ET.parse(filepath)
        root = tree.getroot()
        rows = root.findall('row')
        
        # Vérifications
        missing_location = 0
        missing_dates = 0
        
        for row in rows:
            if row.find('game_location') is None:
                missing_location += 1
            if row.find('game_start_date') is None or row.find('game_end_date') is None:
                missing_dates += 1
        
        if missing_location > 0:
            issues.append(f"{missing_location} jeux sans localisation")
        
        if missing_dates > 0:
            issues.append(f"{missing_dates} jeux sans dates")
        
        status = 'WARNING' if issues else 'OK'
        
        return {
            'status': status,
            'rows': len(rows),
            'issues': issues
        }
    
    def check_excel(self, filepath):
        """Vérifie le fichier Excel"""
        issues = []
        
        df = pd.read_excel(filepath)
        
        # Colonnes requises
        required_cols = ['discipline_title', 'medal_type', 'athlete_full_name']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            issues.append(f"Colonnes manquantes: {missing_cols}")
        
        # Données manquantes
        for col in required_cols:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > len(df) * 0.1:
                    issues.append(f"Trop de donnees manquantes dans '{col}': {missing_count}")
        
        # Types de médailles
        if 'medal_type' in df.columns:
            medal_types = df['medal_type'].dropna().unique()
            valid_types = ['GOLD', 'SILVER', 'BRONZE', 'Gold', 'Silver', 'Bronze']
            invalid_types = [t for t in medal_types if t not in valid_types]
            if invalid_types:
                issues.append(f"Types de medailles invalides: {invalid_types}")
        
        status = 'WARNING' if issues else 'OK'
        
        return {
            'status': status,
            'rows': len(df),
            'issues': issues,
            'columns': len(df.columns)
        }
    
    def check_html(self, filepath):
        """Vérifie le fichier HTML"""
        issues = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        table = soup.find('table')
        
        if not table:
            issues.append("Aucune table trouvee")
            return {'status': 'ERROR', 'issues': issues}
        
        # Conversion en DataFrame
        df = pd.read_html(str(table))[0]
        
        # Vérifications
        if len(df.columns) < 5:
            issues.append(f"Peu de colonnes: {len(df.columns)}")
        
        # Données manquantes
        missing_pct = (df.isna().sum() / len(df) * 100)
        high_missing = missing_pct[missing_pct > 70]
        
        if not high_missing.empty:
            issues.append(f"Colonnes avec beaucoup de donnees manquantes: {len(high_missing)}")
        
        status = 'WARNING' if issues else 'OK'
        
        return {
            'status': status,
            'rows': len(df),
            'issues': issues,
            'columns': len(df.columns)
        }
    
    def generate_summary(self, results):
        """Génère un résumé des vérifications"""
        print("\n" + "="*50)
        print("RESUME DE LA VERIFICATION")
        print("="*50)
        
        total_files = len(results)
        ok_files = sum(1 for r in results.values() if r.get('status') == 'OK')
        warning_files = sum(1 for r in results.values() if r.get('status') == 'WARNING')
        error_files = sum(1 for r in results.values() if r.get('status') == 'ERROR')
        
        print(f"Fichiers verifies: {total_files}")
        print(f"Status OK: {ok_files}")
        print(f"Status WARNING: {warning_files}")
        print(f"Status ERROR: {error_files}")
        
        if error_files > 0:
            print("\nFICHIERS AVEC ERREURS:")
            for filename, result in results.items():
                if result.get('status') == 'ERROR':
                    print(f"  - {filename}: {result.get('error', 'Erreur inconnue')}")
        
        if warning_files > 0:
            print("\nFICHIERS AVEC AVERTISSEMENTS:")
            for filename, result in results.items():
                if result.get('status') == 'WARNING':
                    print(f"  - {filename}: {len(result.get('issues', []))} problemes")
        
        # Recommandation
        print("\nRECOMMANDATION:")
        if error_files > 0:
            print("  Correction manuelle requise pour les fichiers en erreur")
        elif warning_files > 0:
            print("  Integration possible avec nettoyage automatique")
        else:
            print("  Donnees prets pour l'integration")
        
        print("="*50)

if __name__ == "__main__":
    validator = SimpleDataValidator()
    results = validator.check_all_files()
    validator.generate_summary(results)