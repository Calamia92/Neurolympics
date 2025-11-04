# 🚀 Modèle 3 - Équipe Collègue B

## Description
Dossier pour l'approche IA de votre deuxième collègue sur les prédictions JO Paris 2024.

## Structure Attendue
```
model_3_colleague_team/
├── france_predictor.py          # Votre modèle pour médailles France
├── countries_predictor.py       # Votre modèle pour top 25 pays
├── athletes_predictor.py        # Votre modèle pour athlètes individuels
├── model_runner.py             # Script principal d'exécution
├── requirements.txt            # Dépendances spécifiques
└── README.md                   # Documentation
```

## Questions à Répondre
1. **France**: Nombre de médailles Or/Argent/Bronze que gagnera la France ?
2. **Countries**: Classement médailles du Top 25 des pays participants ?
3. **Athletes**: Quels athlètes vont remporter des médailles ?

## Données Disponibles
- **Base commune**: PostgreSQL avec données historiques 1896-2021
- **Athletes 2024**: 1,307 athlètes qualifiés scrapés
- **Accès DB**: Utiliser `src.database.connection.get_db_connection()`

## Approche Suggérée
Vous êtes libre de choisir votre méthode IA :
- Machine Learning classique (scikit-learn)
- Deep Learning (TensorFlow/PyTorch)
- Modèles statistiques avancés
- Ensemble methods
- etc.

## Intégration
Votre `model_runner.py` doit retourner des résultats au format :
```python
{
    'france': {'gold': X, 'silver': Y, 'bronze': Z, 'total': T},
    'countries': [{'country': 'Name', 'predicted_total': N}, ...],
    'athletes': [{'name': 'Name', 'country': 'C', 'probability': P}, ...]
}
```

## TODO
- [ ] Analyser les données disponibles
- [ ] Choisir votre approche IA
- [ ] Développer les 3 modèles prédictifs
- [ ] Tester et valider
- [ ] Documenter votre approche