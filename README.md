# 🏅 Neurolympics - Système de Prédiction Olympique IA

**Projet d'analyse et de prédiction des résultats JO Paris 2024 utilisant l'intelligence artificielle**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)](https://postgresql.org)
[![Flask](https://img.shields.io/badge/Flask-WebApp-orange.svg)](https://flask.palletsprojects.com)
[![ML](https://img.shields.io/badge/ML-XGBoost_V3_Ultra_Realiste-success.svg)](https://xgboost.readthedocs.io)
[![Status](https://img.shields.io/badge/Status-Operationnel-green.svg)]()
[![Version](https://img.shields.io/badge/Version-3.0-brightgreen.svg)]()

📍 **Accès Rapide** : [🌐 WebApp](http://localhost:5000) | [📊 Notebook V3](notebooks/v3_xgboost_prediction.ipynb) | [🤖 Modèle XGBoost](models/xgboost/) | [📖 Docs WebApp](webapp/README.md)

## 🎯 Objectif du Projet

Développer **3 modèles IA différents** pour prédire les résultats des Jeux Olympiques Paris 2024 en répondant à ces questions :

1. **🇫🇷 France** : Nombre de médailles Or/Argent/Bronze que gagnera la France ?
2. **🌍 Countries** : Classement médailles du Top 25 des pays participants ?
3. **🏃 Athletes** : Quels athlètes vont remporter des médailles ?

## 🏗️ Architecture Système

```
Neurolympics/
├── 🤖 models/                          # MODÈLES IA MULTI-ÉQUIPES
│   ├── xgboost/                        # ✅ Modèle XGBoost V3 Ultra-Réaliste (PRINCIPAL)
│   ├── catboost/                       # ✅ Modèle CatBoost V2 (ALTERNATIF)
│   ├── random_forest/                  # ✅ Modèle Random Forest V2 (LEGACY)
│   └── trained/                        # 🎯 Modèles entraînés (.pkl + résultats pré-calculés)
│
├── 🗄️ data/                            # DONNÉES OLYMPIQUES
│   ├── raw/                            # 4 datasets originaux (JSON/XML/XLSX/HTML)
│   ├── exports/                        # Données exportées (CSV)
│   └── cache/                          # Cache web scraping
│
├── 🔧 src/                             # CODE SOURCE COMMUN
│   ├── database/                       # Connexion PostgreSQL optimisée
│   ├── analysis/                       # Analyseurs de données
│   ├── processing/                     # Pipeline ETL avancé
│   └── pipeline/                       # Intégration données
│
├── 🌐 webapp/                          # APPLICATION WEB FLASK
│   ├── app.py                          # 🎯 App Flask avec API REST
│   ├── templates/                      # Interface HTML moderne
│   ├── run.py                          # Lanceur avec diagnostics
│   └── README.md                       # Documentation webapp
│
├── 📊 notebooks/                       # ANALYSES & VISUALISATIONS
│   ├── v3_xgboost_prediction.ipynb     # 🎯 Notebook principal XGBoost V3
│   ├── v1_xgboost_prediction.ipynb     # Versions précédentes
│   ├── v2_xgboost_prediction.ipynb     # Evolution du modèle
│   ├── 01_predictions_olympics_2024.ipynb  # Notebook legacy
│   └── olympic_data_analysis.ipynb     # Analyses complémentaires
│
└── 🚀 scripts/                         # POINTS D'ENTRÉE
    └── run_pipeline.py                 # Pipeline principal automatisé
```

## 🗃️ Base de Données PostgreSQL

**Source de vérité centralisée** pour tous les modèles :

| Table | Records | Description |
|-------|---------|-------------|
| `olympic_results` | 260,458 | Résultats historiques 1896-2021 |
| `olympic_athletes` | 75,904 | Profils athlètes |
| `paris2024_athletes` | 11,110 | **Athlètes qualifiés Paris 2024 (dataset complet)** |
| `olympic_hosts` | 53 | Villes organisatrices |
| `olympic_medals` | 21,697 | Médailles détaillées |

## 🚀 Démarrage Rapide

### 🌐 **Option 1: Interface Web (Recommandée)**
```bash
# 1. Installation des dépendances
pip install -r requirements.txt

# 2. Lancer l'application web
cd webapp
python run.py

# 3. Accéder à l'interface
# 👉 http://localhost:5000
```

### 🤖 **Option 2: Notebook & Ligne de Commande**
```bash
# 1. Tester le modèle XGBoost V3
cd models/xgboost
python olympics_ai_predictor_xgboost.py

# 2. Explorer avec Jupyter
jupyter notebook notebooks/v3_xgboost_prediction.ipynb

# 3. Pipeline complet (legacy)
python scripts/run_pipeline.py
```

### 📋 **Prérequis**
- Python 3.8+
- PostgreSQL avec base configurée
- Connexion internet (pour installation packages)

---

## 🌐 Application Web Flask

### ✨ **Fonctionnalités Web**
L'application web offre une interface moderne et interactive avec :

🏠 **Page d'Accueil**
- Vue d'ensemble du système et statistiques en temps réel
- Métriques principales : 11,110 athlètes, 206 pays, 45 sports

📊 **Exploration des Données**
- Tables interactives avec filtres par pays, sport, nom
- Recherche temps réel d'athlètes avec auto-complétion
- Statistiques détaillées par pays et sport

🤖 **Prédictions IA XGBoost V3**
- **Q1 France** : Visualisation des **58 médailles prédites** (15🥇 21🥈 22🥉)
- **Q2 Top Pays** : USA (124), Chine (106), Australie (88), Allemagne (76), GB (70)
- **Q3 Athlètes** : Top 100 athlètes avec probabilités calibrées

📈 **Visualisations Interactives**
- Graphiques Plotly exportables (PNG, SVG, PDF, HTML)
- Comparaisons historiques vs prédictions 2024
- Distribution géographique et par sport

### 🎨 **Interface Moderne**
- **Design responsive** : Compatible mobile et desktop
- **Thème olympique** : Couleurs or/argent/bronze
- **Navigation intuitive** : Menu moderne avec icônes
- **Animations CSS** : Transitions fluides et loading states

### 🔗 **API REST Intégrée**
```bash
# Endpoints disponibles
GET /api/data/countries          # Liste des pays
GET /api/data/sports            # Liste des sports  
GET /api/search/athletes        # Recherche d'athlètes
GET /api/charts/predictions_*   # Graphiques prédictions
```

### 📱 **Accès Multi-Device**
- **Local** : http://localhost:5000
- **Réseau** : http://[votre-ip]:5000 (accessible depuis autres appareils)
- **Performance** : Temps de chargement < 2s, support 50+ utilisateurs concurrent

## 🤖 Modèles IA Développés

### 🟢 **XGBoost V3 Ultra-Réaliste - MODÈLE PRINCIPAL**
- **Type** : XGBClassifier + CalibratedClassifierCV (calibration isotonique)
- **Approche** : Feature engineering avancé (12 features) + calibration intelligente basée sur délégations
- **Performance** : **ROC-AUC 90.6%**, Accuracy 84.3%
- **Améliorations V3** :
  - ✅ Nombre d'athlètes qualifiés par pays/sport (feature clé)
  - ✅ Ratio médailles/athlètes historique
  - ✅ Calibration basée sur taille des délégations
  - ✅ 250 arbres, profondeur 7, learning rate optimisé
- **Résultats V3** : 
  - 🇫🇷 **France** : **58 médailles** (15🥇 21🥈 22🥉)
  - 🌍 **Top 5 pays** : USA (124), Chine (106), Australie (88), Allemagne (76), GB (70)
  - 🏃 **Athlètes** : Top 100 avec probabilités > 60% pour les meilleurs

### 🟡 **Modèles Alternatifs**
- **CatBoost V2** : Modèle gradient boosting alternatif
- **Random Forest V2** : Modèle legacy (40 médailles France)
- **Documentation** : Voir [`models/DOCUMENTATION.md`](models/DOCUMENTATION.md)

## 📊 Données Disponibles

### 🏛️ Historiques (1896-2021)
- **260K+ résultats** de tous les JO
- **75K+ profils athlètes**
- **21K+ médailles** détaillées

### 🆕 **Paris 2024**
- **11,110 athlètes qualifiés** (données CSV complètes)
- **206 pays participants**
- **45 sports représentés**
- **Données en temps réel** via pipeline automatisé

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

### Installation Complète
```bash
# 1. Dépendances principales
pip install -r requirements.txt

# 2. Dépendances webapp (optionnel)
cd webapp
pip install -r requirements.txt

# 3. Test connexion DB
python -c "from src.database.connection import get_db_connection; print('✅ DB OK' if get_db_connection().test_connection() else '❌ DB Error')"

# 4. Test modèle IA XGBoost V3
python -c "from models.xgboost.olympics_ai_predictor_xgboost import OlympicsAIPredictorXGBoost; print('✅ Modèle XGBoost V3 OK')"
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

## 📈 Résultats Prédictions - XGBoost V3

### 🇫🇷 **France Paris 2024 (V3 Ultra-Réaliste)**
- **Total** : **58 médailles** (+45% vs V2)
- **Détail** : 15 Or, 21 Argent, 22 Bronze
- **Facteurs** : Feature engineering avec athlètes qualifiés + calibration intelligente
- **Méthode** : XGBoost V3 + CalibratedClassifierCV
- **Performance** : ROC-AUC 90.6% (excellente)

### 🌍 **Top 5 Pays (V3 Calibré)**
1. **USA** : 124 médailles (délégation 619 athlètes)
2. **Chine** : 106 médailles (délégation 398 athlètes)
3. **Australie** : 88 médailles (délégation 475 athlètes)
4. **Allemagne** : 76 médailles (délégation 457 athlètes)
5. **Grande-Bretagne** : 70 médailles (délégation 342 athlètes)

### 🏃 **Athlètes Individuels (V3 Sophistiqué)**
- **11,110 athlètes analysés** (dataset complet)
- **Top 100** les plus prometteurs identifiés
- **1,044 médailles totales** estimées (réaliste)
- **Probabilités calibrées** (60-70% pour top athlètes Beach Volleyball USA)

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
| 🤖 XGBoost V3 | ✅ Opérationnel | ROC-AUC 90.6% |
| 🤖 CatBoost V2 | ✅ Opérationnel | Modèle alternatif |
| 🤖 Random Forest V2 | ✅ Legacy | Modèle de référence |
| 📊 Visualisations | ✅ Opérationnel | Jupyter notebook |
| 🗃️ Base PostgreSQL | ✅ Opérationnel | Tables optimisées |

## 🆕 Nouveautés Version V3

### ✨ **Révolution XGBoost V3 Ultra-Réaliste**
- **🧠 Feature Engineering Avancé** : 12 variables sophistiquées vs 7 précédemment
- **📊 Athlètes Qualifiés Intégrés** : Utilisation du nombre d'athlètes par pays/sport (feature clé)
- **🎯 Calibration Intelligente** : Basée sur la taille des délégations
- **⚡ Mode Ultra-Rapide** : Résultats pré-calculés pour webapp instantanée
- **📈 Performance Exceptionnelle** : ROC-AUC 90.6% vs 84.3% précédemment

### 🆚 **Evolution des Prédictions France**
| Version | Médailles | Amélioration | Méthodologie |
|---------|-----------|--------------|--------------|
| V1 Random Forest | 34 médailles | Base | Boost simple 1.25x |
| V2 Random Forest | 40 médailles | +18% | Boost 1.5x + pondération |
| **V3 XGBoost** | **58 médailles** | **+71%** | **Feature engineering + calibration intelligente** |

### 🔧 **Innovations Techniques V3**
| Amélioration | Impact |
|-------------|---------|
| ✅ Nombre d'athlètes qualifiés par sport | Feature la plus importante |
| ✅ Ratio médailles/athlètes historique | Prédictions plus réalistes |
| ✅ Calibration basée délégations | USA/Chine mieux positionnés |
| ✅ XGBoost 250 arbres (profondeur 7) | Modèle plus complexe |
| ✅ Résultats pré-calculés (.pkl) | Webapp ultra-rapide |

### 🎯 **Performance V3**
- **ROC-AUC Score** : 90.6% (excellent)
- **Accuracy** : 84.3% (maintenu)
- **Temps Prédiction** : Instantané (pré-calculé)
- **Features** : 12 variables avancées
- **Total Médailles** : 1,044 (réaliste)

## 🔬 Détails Techniques

### 🧠 **Intelligence Artificielle XGBoost V3**
```python
# Architecture Modèle V3 Ultra-Réaliste
XGBClassifier(
    n_estimators=250,
    max_depth=7,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    reg_alpha=0.2,
    reg_lambda=0.5,
    gamma=0.05,
    min_child_weight=3
) + CalibratedClassifierCV(method='isotonic')

# Features Engineering Avancé (12 variables)
- total_medals_hist              # Médailles historiques pondérées
- gold_count, silver_count       # Médailles par type
- medals_in_sport               # Force historique sport-pays
- unique_medalists_hist         # Nombre d'athlètes médaillés historique
- medal_per_athlete_ratio       # Efficacité médailles/athlète
- athlete_count                 # 🎯 NOUVEAU: Athlètes qualifiés 2024
- expected_medals_from_athletes # 🎯 NOUVEAU: Médailles attendues basées athlètes
- discipline_enc, country_enc   # Encodages catégoriels
```

### 🗃️ **Base de Données PostgreSQL**
```sql
-- Schema Optimisé
CREATE INDEX idx_athletes_country ON paris2024_athletes(country);
CREATE INDEX idx_results_medal ON olympic_results(medal_type);
CREATE INDEX idx_athletes_sport ON paris2024_athletes(sport);

-- Performance Queries
-- Recherche athlètes : < 50ms
-- Agrégations pays : < 100ms  
-- Prédictions batch : < 2s
```

### 🚀 **Stack Technique V3**
- **Backend** : Python 3.8+, Flask, SQLAlchemy
- **Machine Learning** : **XGBoost**, scikit-learn, pandas, numpy
- **Frontend** : HTML5, Bootstrap 5, Plotly.js
- **Base de Données** : PostgreSQL avec index optimisés
- **Visualisations** : Plotly, matplotlib, seaborn
- **Déploiement** : Gunicorn ready, Docker compatible
- **Performance** : Résultats pré-calculés (.pkl) pour webapp ultra-rapide

## 🚀 Prochaines Étapes

1. **🔬 Modèles Ensemble** - Combinaison XGBoost V3 + CatBoost + Random Forest
2. **📊 Dashboard Temps Réel** - Mise à jour prédictions pendant les JO
3. **🔄 Apprentissage Continu** - Recalibrage modèle avec résultats réels
4. **📱 Application Mobile** - PWA avec prédictions XGBoost V3
5. **☁️ Déploiement Cloud** - AWS/Azure pour scalabilité mondiale
6. **🔗 API Publique** - Endpoints XGBoost V3 pour développeurs tiers
7. **🎯 Optimisation V4** - Deep Learning avec réseaux de neurones

---

**🏆 Système de prédiction olympique révolutionnaire avec XGBoost V3 Ultra-Réaliste - 58 médailles France prédites !**

*Pour plus de détails : [`models/DOCUMENTATION.md`](models/DOCUMENTATION.md) | [`webapp/README.md`](webapp/README.md)*