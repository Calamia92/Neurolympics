# 🏅 Neurolympics - Système de Prédiction Olympique IA

**Projet d'analyse et de prédiction des résultats JO Paris 2024 utilisant l'intelligence artificielle**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)](https://postgresql.org)
[![Status](https://img.shields.io/badge/Status-Operationnel-green.svg)]()

## 🎯 Objectif du Projet

Développer **3 modèles IA différents** pour prédire les résultats des Jeux Olympiques Paris 2024 en répondant à ces questions :

1. **🇫🇷 France** : Nombre de médailles Or/Argent/Bronze que gagnera la France ?
2. **🌍 Countries** : Classement médailles du Top 25 des pays participants ?
3. **🏃 Athletes** : Quels athlètes vont remporter des médailles ?

## 🏗️ Architecture Système

```
Neurolympics/
├── 🤖 models/                          # 3 MODÈLES IA (équipes séparées)
│   ├── model_1/                        # ✅ Modèle opérationnel
│   ├── model_2/                        # 🚧 Équipe collègue A
│   └── model_3/                        # 🚧 Équipe collègue B
│
├── 🗄️ data/                            # DONNÉES OLYMPIQUES
│   ├── raw/                            # 4 datasets originaux (JSON/XML/XLSX/HTML)
│   ├── scraped/                        # Données Paris 2024 (1,307 athlètes)
│   └── cache/                          # Cache web scraping
│
├── 🔧 src/                             # CODE SOURCE COMMUN
│   ├── database/                       # Connexion PostgreSQL
│   ├── scraping/                       # Web scraping automatisé
│   ├── processing/                     # Pipeline ETL
│   └── pipeline/                       # Intégration données
│
├── 📊 notebooks/                       # ANALYSES & VISUALISATIONS
│   └── 01_predictions_olympics_2024.ipynb
│
└── 🚀 scripts/                         # POINTS D'ENTRÉE
    ├── run_pipeline.py                 # Pipeline principal
    └── run_scraping_pipeline.py        # Scraping automatisé
```

## 🗃️ Base de Données PostgreSQL

**Source de vérité centralisée** pour tous les modèles :

| Table | Records | Description |
|-------|---------|-------------|
| `olympic_results` | 260,458 | Résultats historiques 1896-2021 |
| `olympic_athletes` | 75,904 | Profils athlètes |
| `scraped_athletes_2024` | 1,307 | Athlètes qualifiés Paris 2024 |
| `olympic_hosts` | 53 | Villes organisatrices |
| `olympic_medals` | 21,697 | Médailles détaillées |

## 🚀 Utilisation Rapide

### 1. Exécuter le modèle IA opérationnel
```bash
cd models/model_1
python final_predictions_summary.py
```

### 2. Lancer le pipeline complet
```bash
python scripts/run_pipeline.py
```

### 3. Enrichir avec scraping
```bash
python scripts/run_scraping_pipeline.py --scraper all
```

### 4. Explorer avec Jupyter
```bash
jupyter notebook notebooks/01_predictions_olympics_2024.ipynb
```

## 🤖 Modèles IA Développés

### 🟢 Modèle 1 - Opérationnel
- **Équipe** : Votre équipe
- **Approche** : Analyse historique + facteurs 2024
- **Résultats** : 
  - France : 40 médailles (12🥇 13🥈 15🥉)
  - Top 3 pays : USA, France, Allemagne
  - Athletes : 156 médailles estimées

### 🟡 Modèle 2 & 3 - En développement
- **Équipes** : Collègues A & B
- **Status** : Placeholders créés, prêts à implémenter
- **Documentation** : Voir [`models/DOCUMENTATION.md`](models/DOCUMENTATION.md)

## 📊 Données Disponibles

### 🏛️ Historiques (1896-2021)
- **260K+ résultats** de tous les JO
- **75K+ profils athlètes**
- **21K+ médailles** détaillées

### 🆕 Paris 2024
- **1,307 athlètes qualifiés** (scraping Wikipedia)
- **229 athlètes français**
- **12 pays principaux** couverts

## ⚙️ Configuration

### Variables d'environnement
```bash
# Base de données
DATABASE_URL=postgresql://user:password@host:port/database

# Ou séparément :
DB_HOST=localhost
DB_PORT=5432
DB_NAME=neurolympics
DB_USER=postgres
DB_PASSWORD=your_password
```

### Installation
```bash
# Dépendances
pip install -r requirements.txt

# Test connexion DB
python -c "from src.database.connection import get_db_connection; print('✅ DB OK' if get_db_connection().test_connection() else '❌ DB Error')"
```

## 🔄 Pipeline Automatisé

Le système exécute automatiquement :

1. **🔍 VALIDATION** - Qualité des 4 datasets
2. **🔗 CONNEXION** - Test PostgreSQL
3. **🔄 TRANSFORMATION** - Normalisation formats
4. **🏗️ SCHEMA** - Création tables
5. **📥 CHARGEMENT** - 260K+ enregistrements
6. **🕷️ SCRAPING** - Enrichissement 2024
7. **🤖 PRÉDICTIONS** - Modèles IA
8. **📊 VISUALISATION** - Rapports Jupyter

## 📈 Résultats Prédictions

### 🇫🇷 **France Paris 2024**
- **Total** : 40 médailles
- **Détail** : 12 Or, 13 Argent, 15 Bronze
- **Facteurs** : Pays hôte + 229 athlètes qualifiés

### 🌍 **Top 5 Pays**
1. **USA** : 1,040 médailles
2. **France** : 439 médailles
3. **Allemagne** : 350 médailles
4. **Grande-Bretagne** : 277 médailles
5. **Italie** : 258 médailles

### 🏃 **Athlètes Individuels**
- **941 athlètes analysés**
- **Top probabilité** : USA (24.8%)
- **156 médailles estimées** au total

## 🛠️ Développement

### Structure modulaire
- **Modèles IA** : `models/model_X/`
- **Code commun** : `src/`
- **Tests** : `tests/`
- **Documentation** : `models/DOCUMENTATION.md`

### Ajouter un nouveau modèle
1. Créer dossier `models/model_X/`
2. Implémenter les 3 prédicteurs
3. Utiliser format de sortie standard
4. Tester avec PostgreSQL

## 📋 Status Projet

| Composant | Status | Description |
|-----------|--------|-------------|
| 📊 Pipeline ETL | ✅ Opérationnel | 260K+ records intégrés |
| 🕷️ Web Scraping | ✅ Opérationnel | 1,307 athlètes 2024 |
| 🤖 Modèle IA #1 | ✅ Opérationnel | Prédictions validées |
| 🤖 Modèle IA #2 | 🚧 En attente | Placeholders créés |
| 🤖 Modèle IA #3 | 🚧 En attente | Placeholders créés |
| 📊 Visualisations | ✅ Opérationnel | Jupyter notebook |
| 🗃️ Base PostgreSQL | ✅ Opérationnel | Tables optimisées |

## 🚀 Prochaines Étapes

1. **Compléter modèles 2 & 3** - Implémentation collègues
2. **Comparaison multi-modèles** - Analyse écarts
3. **Validation post-JO** - Mesure performance réelle
4. **Optimisation continue** - Apprentissage résultats

---

**🏆 Système complet de prédiction olympique opérationnel avec IA multi-modèles !**

*Pour plus de détails sur les modèles : [`models/DOCUMENTATION.md`](models/DOCUMENTATION.md)*