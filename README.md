# Neurolympics - Analyse des Données Olympiques

Projet d'analyse et d'intégration des données olympiques avec pipeline de traitement automatisé.

## 🏗️ Structure du Projet

```
Neurolympics/
├── data/                           # Données du projet
│   ├── raw/                        # Données brutes originales
│   │   ├── olympic_athletes.json   # 75,904 athlètes
│   │   ├── olympic_hosts.xml       # 53 jeux olympiques
│   │   ├── olympic_medals.xlsx     # 21,697 médailles
│   │   └── olympic_results.html    # 162,804 résultats
│   ├── processed/                  # Données transformées
│   └── exports/                    # Exports et rapports
├── src/                            # Code source
│   ├── database/                   # Connexion base de données
│   │   └── connection.py
│   ├── processing/                 # Traitement des données
│   │   ├── validator.py           # Validation qualité
│   │   └── transformer.py         # Transformation
│   └── pipeline/                   # Pipeline d'intégration
│       └── integration.py
├── notebooks/                      # Notebooks Jupyter
│   └── olympic_data_analysis.ipynb
├── scripts/                        # Scripts d'exécution
│   └── run_pipeline.py            # Point d'entrée principal
├── config/                         # Configuration
│   └── settings.py
├── tests/                          # Tests unitaires
└── requirements.txt               # Dépendances Python
```

## 🚀 Utilisation

### 1. Point d'entrée principal
```bash
python scripts/run_pipeline.py
```

### 2. Validation seule des données
```bash
python -m src.processing.validator
```

### 3. Transformation seule
```bash
python -m src.processing.transformer
```

## 📊 Pipeline de Traitement

Le pipeline exécute automatiquement ces étapes :

1. **🔍 VALIDATION** - Vérification qualité des données
2. **🔗 CONNEXION** - Test connexion base de données
3. **🔄 TRANSFORMATION** - Normalisation des 4 formats
4. **🏗️ SCHEMA** - Création tables PostgreSQL
5. **📥 CHARGEMENT** - Insertion données transformées
6. **✅ VERIFICATION** - Contrôles qualité finaux

## 🗄️ Base de Données

Tables créées automatiquement :
- `olympic_athletes` - Profils des athlètes
- `olympic_hosts` - Villes et dates des jeux
- `olympic_medals` - Médailles par épreuve
- `olympic_results` - Résultats détaillés

## ⚙️ Configuration

Variables d'environnement requises :
```bash
DATABASE_URL=postgresql://user:password@host:port/database
# OU
DB_HOST=localhost
DB_PORT=5432
DB_NAME=neurolympics
DB_USER=postgres
DB_PASSWORD=your_password
```

## 📋 Statut Qualité Actuel

✅ **olympic_athletes.json** - 75,904 athlètes (OK)  
✅ **olympic_hosts.xml** - 53 jeux olympiques (OK)  
⚠️ **olympic_medals.xlsx** - 21,697 médailles (3,624 noms manquants)  
⚠️ **olympic_results.html** - 162,804 résultats (colonnes incomplètes)

**Recommandation : Intégration possible avec nettoyage automatique**

## 🛠️ Développement

Pour ajouter de nouvelles fonctionnalités :
1. Modules dans `src/`
2. Tests dans `tests/`
3. Configuration dans `config/settings.py`
4. Point d'entrée via `scripts/`