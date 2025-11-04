"""
Modele predictif pour identifier les athletes individuels
qui ont le plus de chances de remporter des medailles a Paris 2024
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.connection import get_db_connection
import pandas as pd
import random

class IndividualAthletesPredictor:
    """Modele de prediction des athletes individuels medailles"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def get_athletes_2024_by_country(self):
        """Recupere athletes 2024 par pays"""
        query = """
        SELECT 
            name,
            country,
            sport,
            source,
            type
        FROM scraped_athletes_2024 
        WHERE qualified_2024 = true 
        AND type = 'national_team_wikipedia'
        AND LENGTH(name) > 3
        ORDER BY country, name
        """
        
        result = self.db.execute_query(query)
        return result
    
    def get_historical_medal_patterns_by_country(self):
        """Analyse patterns historiques par pays"""
        query = """
        SELECT 
            country_name,
            discipline,
            COUNT(*) as medals_in_sport
        FROM olympic_results 
        WHERE medal_type IN ('GOLD', 'SILVER', 'BRONZE')
        GROUP BY country_name, discipline
        HAVING COUNT(*) >= 5
        ORDER BY country_name, medals_in_sport DESC
        """
        
        result = self.db.execute_query(query)
        return result
    
    def calculate_athlete_medal_probability(self, athlete_data, country_patterns):
        """Calcule la probabilite qu'un athlete gagne une medaille"""
        
        country = athlete_data['country']
        sport = athlete_data['sport']
        name = athlete_data['name']
        
        # Score de base par pays (performance historique)
        country_scores = {
            'United States': 0.25,  # 25% chance base
            'France': 0.20,         # Pays hote boost
            'Germany': 0.18,
            'Great Britain': 0.17,
            'Italy': 0.16,
            'Australia': 0.15,
            'Japan': 0.15,
            'Canada': 0.14,
            'Netherlands': 0.16,
            'Spain': 0.12,
            'China': 0.22,
            'Brazil': 0.10
        }
        
        base_prob = country_scores.get(country, 0.08)  # Default 8%
        
        # Boost sport (sports avec plus de medailles disponibles)
        sport_multipliers = {
            'Athletics': 1.3,      # Beaucoup d'epreuves
            'Swimming': 1.2,       # Beaucoup d'epreuves
            'Gymnastics': 1.1,
            'Cycling': 1.1,
            'Wrestling': 1.0,
            'Boxing': 1.0,
            'Judo': 0.9,
            'Tennis': 0.8,         # Peu d'epreuves
            'Basketball': 0.7,     # 2 medailles seulement
            'Football': 0.6        # 2 medailles seulement
        }
        
        sport_key = sport if sport else 'Unknown'
        sport_multiplier = sport_multipliers.get(sport_key, 0.9)
        
        # Boost historique du pays dans ce sport
        country_sport_patterns = country_patterns[
            (country_patterns['country_name'] == country) &
            (country_patterns['discipline'].str.contains(sport_key, case=False, na=False))
        ] if sport_key != 'Unknown' else pd.DataFrame()
        
        if not country_sport_patterns.empty:
            historical_boost = 1.2  # +20% si le pays a de l'historique dans ce sport
        else:
            historical_boost = 1.0
        
        # Facteurs speciaux pour certains athletes/pays
        special_boosts = {
            'France': 1.15,  # Pays hote
            'United States': 1.1,  # Puissance sportive
            'China': 1.05,   # Preparation intensive
        }
        
        special_boost = special_boosts.get(country, 1.0)
        
        # Calcul final
        final_probability = base_prob * sport_multiplier * historical_boost * special_boost
        
        # Cap a 60% max
        final_probability = min(final_probability, 0.60)
        
        return {
            'probability': final_probability,
            'base_prob': base_prob,
            'sport_multiplier': sport_multiplier,
            'historical_boost': historical_boost,
            'special_boost': special_boost
        }
    
    def predict_individual_medalists_2024(self):
        """Prediction des athletes individuels pour medailles"""
        
        print("=== PREDICTION ATHLETES INDIVIDUELS PARIS 2024 ===")
        print()
        
        # Charger donnees
        athletes_2024 = self.get_athletes_2024_by_country()
        country_patterns = self.get_historical_medal_patterns_by_country()
        
        print(f"Athletes qualifies analyses: {len(athletes_2024)}")
        print(f"Patterns historiques charges: {len(country_patterns)} combinaisons pays-sport")
        print()
        
        # Calculer probabilites pour chaque athlete
        predictions = []
        
        for _, athlete in athletes_2024.iterrows():
            prob_data = self.calculate_athlete_medal_probability(athlete, country_patterns)
            
            predictions.append({
                'name': athlete['name'],
                'country': athlete['country'], 
                'sport': athlete['sport'] if athlete['sport'] else 'Unknown',
                'medal_probability': prob_data['probability'],
                'medal_probability_pct': prob_data['probability'] * 100,
                'base_prob': prob_data['base_prob'],
                'sport_boost': prob_data['sport_multiplier'],
                'historical_boost': prob_data['historical_boost'],
                'special_boost': prob_data['special_boost']
            })
        
        # Trier par probabilite
        predictions.sort(key=lambda x: x['medal_probability'], reverse=True)
        
        # Top athletes par probabilite
        print("TOP 30 ATHLETES AVEC PLUS DE CHANCES DE MEDAILLE:")
        print("=" * 85)
        print(f"{'#':<3} {'ATHLETE':<25} {'PAYS':<15} {'SPORT':<12} {'CHANCE':<8}")
        print("-" * 85)
        
        top_athletes = []
        for i, athlete in enumerate(predictions[:30], 1):
            name = athlete['name'][:24] if len(athlete['name']) > 24 else athlete['name']
            country = athlete['country'][:14] if len(athlete['country']) > 14 else athlete['country']
            sport = athlete['sport'][:11] if len(athlete['sport']) > 11 else athlete['sport']
            chance = f"{athlete['medal_probability_pct']:.1f}%"
            
            print(f"{i:<3} {name:<25} {country:<15} {sport:<12} {chance:<8}")
            
            top_athletes.append(athlete)
        
        print("-" * 85)
        print()
        
        # Statistiques par pays
        country_stats = {}
        for pred in predictions:
            country = pred['country']
            if country not in country_stats:
                country_stats[country] = {
                    'total_athletes': 0,
                    'avg_probability': 0,
                    'top_athletes': 0
                }
            
            country_stats[country]['total_athletes'] += 1
            country_stats[country]['avg_probability'] += pred['medal_probability']
            
            if pred['medal_probability'] > 0.20:  # Plus de 20% de chance
                country_stats[country]['top_athletes'] += 1
        
        # Calculer moyennes
        for country in country_stats:
            total = country_stats[country]['total_athletes']
            if total > 0:
                country_stats[country]['avg_probability'] /= total
        
        # Afficher stats pays
        print("STATISTIQUES PAR PAYS (TOP 10):")
        print("-" * 60)
        print(f"{'PAYS':<20} {'ATHLETES':<10} {'CHANCE MOY':<12} {'TOP CHANCES':<12}")
        print("-" * 60)
        
        sorted_countries = sorted(
            country_stats.items(), 
            key=lambda x: x[1]['avg_probability'], 
            reverse=True
        )
        
        for country, stats in sorted_countries[:10]:
            if stats['total_athletes'] >= 10:  # Au moins 10 athletes
                country_name = country[:19] if len(country) > 19 else country
                total = stats['total_athletes']
                avg_prob = f"{stats['avg_probability']*100:.1f}%"
                top_count = stats['top_athletes']
                
                print(f"{country_name:<20} {total:<10} {avg_prob:<12} {top_count:<12}")
        
        print("-" * 60)
        print()
        
        # Estimation nombre total de medailles
        total_expected_medals = sum(pred['medal_probability'] for pred in predictions)
        
        print("RESUME PREDICTIONS:")
        print(f"  - Athletes analyses: {len(predictions)}")
        print(f"  - Medailles totales estimees: {total_expected_medals:.1f}")
        print(f"  - Athletes avec >20% chance: {len([p for p in predictions if p['medal_probability'] > 0.20])}")
        print(f"  - Athletes avec >30% chance: {len([p for p in predictions if p['medal_probability'] > 0.30])}")
        
        # Top 5 par pays
        print()
        print("TOP 5 ATHLETES PAR PAYS PRINCIPAL:")
        main_countries = ['United States', 'France', 'Germany', 'Great Britain', 'Italy']
        
        for country in main_countries:
            country_athletes = [p for p in predictions if p['country'] == country][:5]
            if country_athletes:
                print(f"\\n{country}:")
                for i, athlete in enumerate(country_athletes, 1):
                    name = athlete['name']
                    sport = athlete['sport']
                    chance = athlete['medal_probability_pct']
                    print(f"  {i}. {name} ({sport}): {chance:.1f}%")
        
        return {
            'top_30_athletes': top_athletes,
            'all_predictions': predictions,
            'country_statistics': country_stats,
            'total_expected_medals': total_expected_medals,
            'methodology': 'Probabiliste base sur historique pays + sport + facteurs 2024'
        }

if __name__ == "__main__":
    if get_db_connection().test_connection():
        predictor = IndividualAthletesPredictor()
        results = predictor.predict_individual_medalists_2024()
        
        print()
        print("PREDICTION ATHLETES INDIVIDUELS TERMINEE!")
        top_3 = results['top_30_athletes'][:3]
        print(f"Top 3: {', '.join([a['name'] + ' (' + str(round(a['medal_probability_pct'], 1)) + '%)' for a in top_3])}")
    else:
        print("ERREUR: Connexion base de donnees")