# 🏅 Modèle 1 - Votre Équipe

## Description
Ce dossier contient votre approche IA pour prédire les résultats des JO Paris 2024.

## Vos Modèles
- **France**: `simple_france_predictor.py` - Prédiction médailles françaises
- **Countries**: `top25_countries_predictor.py` - Classement top 25 pays
- **Athletes**: `individual_athletes_predictor.py` - Prédictions athlètes individuels
- **Summary**: `final_predictions_summary.py` - Rapport final

## Approche Technique
- **Méthode**: Analyse historique + facteurs 2024
- **Base de données**: PostgreSQL avec 260K+ enregistrements
- **Données 2024**: 1,307 athlètes scrapés

## Utilisation
```bash
# Prédiction France
python simple_france_predictor.py

# Prédiction Top 25 pays
python top25_countries_predictor.py

# Prédiction athlètes individuels
python individual_athletes_predictor.py

# Rapport complet
python final_predictions_summary.py
```

## Résultats
- **France**: 40 médailles (12 Or, 13 Argent, 15 Bronze)
- **Top 3 pays**: USA, France, Allemagne
- **Athletes**: 156 médailles estimées

## Confiance
- **France**: ⭐⭐⭐⭐⭐ Très haute
- **Countries**: ⭐⭐⭐⭐ Haute
- **Athletes**: ⭐⭐⭐ Moyenne