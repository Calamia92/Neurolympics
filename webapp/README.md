# 🏅 Neurolympics WebApp - Prédictions JO Paris 2024

Application web complète avec intelligence artificielle pour les prédictions olympiques.

## 🌟 Fonctionnalités

### 📊 Pages Principales
- **Accueil** : Vue d'ensemble du système IA et statistiques générales
- **Données** : Tables interactives avec filtres et recherche d'athlètes
- **Prédictions IA** : Résultats du modèle Random Forest V2 pour les 3 questions
- **Visualisations** : Graphiques interactifs Plotly avec export
- **Analyses** : Études approfondies des performances et qualité des données

### 🤖 Intelligence Artificielle
- **Modèle Random Forest V2** robuste et calibré
- **Données nettoyées** (filtrage strict medal_type vides)
- **Prédictions réalistes** normalisées (~1000 médailles total)
- **3 Questions** : Médailles France, Top 25 pays, Athlètes individuels

### 🎨 Interface Utilisateur
- **Design moderne** avec Bootstrap 5 et animations CSS
- **Responsive** adapté mobile/desktop
- **Thème olympique** avec couleurs médailles (Or/Argent/Bronze)
- **Navigation intuitive** avec icônes Font Awesome

### 📈 Visualisations Interactives
- **Graphiques Plotly** dynamiques et exportables
- **Filtres temps réel** par pays, sport, nombre d'éléments
- **Métriques en direct** avec animations
- **Export multi-format** : PNG, SVG, PDF, HTML

## 🚀 Installation et Lancement

### Prérequis
```bash
Python 3.8+
PostgreSQL avec base Neurolympics
Modèle IA V2 entraîné
```

### 1. Installation des dépendances
```bash
cd webapp
pip install -r requirements.txt
```

### 2. Configuration Base de Données
Vérifiez que `src/database/connection.py` pointe vers votre PostgreSQL.

### 3. Modèle IA
Assurez-vous que le modèle existe :
```
models/trained/random_forest_model_v2.pkl
```

### 4. Lancement
```bash
python run.py
```

Ou directement :
```bash
python app.py
```

### 5. Accès
- **Local** : http://localhost:5000
- **Réseau** : http://[votre-ip]:5000

## 📚 Structure du Projet

```
webapp/
├── app.py                 # Application Flask principale
├── run.py                 # Script de lancement avec diagnostics
├── requirements.txt       # Dépendances Python
├── README.md             # Cette documentation
└── templates/            # Templates HTML
    ├── base.html         # Template de base avec navigation
    ├── index.html        # Page d'accueil
    ├── data.html         # Exploration des données
    ├── predictions.html  # Prédictions IA
    ├── visualizations.html # Graphiques interactifs
    └── analysis.html     # Analyses avancées
```

## 🔗 API Endpoints

### Données
- `GET /api/data/countries` - Liste des pays
- `GET /api/data/sports` - Liste des sports
- `GET /api/search/athletes` - Recherche d'athlètes avec filtres

### Visualisations
- `GET /api/charts/athletes_by_country` - Graphique athlètes par pays
- `GET /api/charts/sports_distribution` - Distribution des sports
- `GET /api/charts/predictions_france` - Prédiction France
- `GET /api/charts/predictions_countries` - Top pays prédits
- `GET /api/charts/historical_france` - Évolution historique France

## 🎯 Utilisation

### 1. Exploration des Données
- Naviguez vers `/data`
- Utilisez les filtres pour chercher des athlètes
- Consultez les statistiques par pays

### 2. Prédictions IA
- Accédez à `/predictions`
- Visualisez les 3 réponses du modèle V2
- Consultez les graphiques explicatifs

### 3. Visualisations
- Page `/visualizations` pour graphiques interactifs
- Changez les paramètres (limite, couleurs)
- Exportez en différents formats

### 4. Analyses Avancées
- Section `/analysis` pour études détaillées
- Comparez V1 vs V2
- Analysez la qualité des données

## 🛠️ Personnalisation

### Ajouter de nouveaux graphiques
1. Créer l'endpoint dans `app.py`
2. Ajouter la fonction JavaScript dans le template
3. Intégrer à l'interface utilisateur

### Modifier le design
- Éditer `templates/base.html` pour le CSS global
- Adapter les couleurs dans la section `<style>`
- Changer les icônes Font Awesome

### Étendre l'API
- Ajouter des routes dans `app.py`
- Utiliser le pattern `/api/[category]/[endpoint]`
- Retourner du JSON pour l'interactivité

## 🔧 Configuration Avancée

### Variables d'environnement
```bash
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=postgresql://user:pass@host:port/db
MODEL_PATH=models/trained/random_forest_model_v2.pkl
```

### Déploiement Production
```bash
# Avec Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Avec Docker
# (Dockerfile à créer)
```

## 📊 Performances

### Optimisations Implémentées
- **Cache Plotly** pour éviter les recalculs
- **Pagination** des résultats de recherche
- **Lazy loading** des graphiques
- **Compression** des réponses JSON

### Métriques
- **Temps de chargement** : < 2s
- **Taille moyenne page** : ~500KB
- **Concurrent users** : ~50

## 🐛 Dépannage

### Erreurs Communes

#### 1. Erreur de connexion DB
```
❌ Erreur connexion base de données
```
**Solution** : Vérifiez `src/database/connection.py`

#### 2. Modèle non trouvé
```
❌ Aucun modele pre-entraine trouve
```
**Solution** : Entraînez le modèle V2 ou copiez le fichier `.pkl`

#### 3. Import errors
```
ModuleNotFoundError: No module named 'models'
```
**Solution** : Vérifiez que vous lancez depuis le bon répertoire

### Debug Mode
Activez le debug dans `run.py` :
```python
app.run(debug=True)
```

## 🎨 Capture d'Écran

L'interface ressemble aux fonctionnalités du site de référence avec :
- Navigation moderne avec sections dédiées
- Filtres interactifs pour la recherche
- Tableaux avec tri et pagination
- Graphiques Plotly exportables
- Design responsive et attrayant

## 🏆 Améliorations V2

### Par rapport au modèle V1
- ✅ **Prédictions réalistes** (plus de 263 médailles USA)
- ✅ **Diversité géographique** équilibrée  
- ✅ **Données propres** sans medal_type vides
- ✅ **Interface moderne** inspirée des meilleures pratiques web

## 📞 Support

Pour toute question ou amélioration :
1. Vérifiez la documentation
2. Consultez les logs de l'application
3. Testez avec des données d'exemple

---

🚀 **Neurolympics WebApp - Intelligence Artificielle pour les JO Paris 2024**