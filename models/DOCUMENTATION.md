# 📚 Documentation Modèles IA

## Structure du Projet

Ce projet contient **3 modèles différents** développés par **3 équipes séparées** pour répondre aux mêmes questions olympiques :

```
models/
├── model_1/                    # 🟢 ÉQUIPE 1 - Modèle opérationnel
├── model_2/                    # 🟡 ÉQUIPE 2 - Placeholders à implémenter  
└── model_3/                    # 🟡 ÉQUIPE 3 - Placeholders à implémenter
```

## 🎯 Questions Communes (3 équipes)

Chaque équipe doit répondre aux **3 mêmes questions** avec son approche IA :

1. **France** : Nombre de médailles Or/Argent/Bronze que gagnera la France ?
2. **Countries** : Classement médailles du Top 25 des pays participants ?
3. **Athletes** : Quels athlètes vont remporter des médailles ?

## 🏗️ Architecture par Équipe

### Modèle 1 - Votre Équipe ✅
- **Status** : Opérationnel  
- **Approche** : Analyse historique + facteurs 2024
- **Fichiers** : `simple_france_predictor.py`, `top25_countries_predictor.py`, `individual_athletes_predictor.py`
- **Résultats** : France 40 médailles, USA en tête, 156 médailles athlètes estimées

### Modèle 2 - Collègue A 🚧
- **Status** : Placeholders créés
- **À faire** : Implémenter approche IA différente
- **Fichiers** : `france_predictor.py`, `countries_predictor.py`, `athletes_predictor.py`

### Modèle 3 - Collègue B 🚧  
- **Status** : Placeholders créés
- **À faire** : Implémenter approche IA différente
- **Fichiers** : `france_predictor.py`, `countries_predictor.py`, `athletes_predictor.py`

## 📊 Données Communes

Toutes les équipes ont accès aux **mêmes données** :
- **Base PostgreSQL** : 260K+ résultats historiques (1896-2021)
- **Athletes 2024** : 1,307 athlètes qualifiés scrapés
- **Connexion** : `src.database.connection.get_db_connection()`

## 🚀 Utilisation

### Exécuter Modèle 1 (Votre équipe)
```bash
cd models/model_1
python final_predictions_summary.py
```

### Exécuter Modèle 2 (Collègue A)
```bash
cd models/model_2
python model_runner.py  # TODO: Implémenter
```

### Exécuter Modèle 3 (Collègue B)
```bash
cd models/model_3
python model_runner.py  # TODO: Implémenter
```

## 🔄 Comparaison Future

Une fois les 3 modèles implémentés, vous pourrez :
- Comparer les approches IA différentes
- Analyser les écarts de prédictions
- Évaluer la performance relative
- Créer ensemble final combiné

## 📝 Format de Sortie Standard

Chaque modèle doit retourner :
```python
{
    'france': {'gold': X, 'silver': Y, 'bronze': Z, 'total': T},
    'countries': [{'country': 'Name', 'predicted_total': N}, ...],
    'athletes': [{'name': 'Name', 'country': 'C', 'probability': P}, ...]
}
```

---

**Votre code IA est organisé dans `model_1_your_team/` ✅**  
**Vos collègues peuvent développer dans `model_2_colleague_team/` et `model_3_colleague_team/` 🚧**