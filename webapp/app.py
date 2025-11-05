"""
WEBAPP NEUROLYMPICS - PRÉDICTIONS JO PARIS 2024
Application Flask complète avec modèle IA V2
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, render_template, jsonify, request
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
import json
from datetime import datetime

from models.random_forest.olympics_ai_predictor_v2 import OlympicsAIPredictorV2
from src.database.connection import get_db_connection

app = Flask(__name__)
app.config['SECRET_KEY'] = 'neurolympics-2024-paris'

# Ajouter un filtre personnalisé pour les nombres
@app.template_filter('number_format')
def number_format(value):
    """Formate les nombres avec des séparateurs de milliers"""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value

# Variables globales
predictor = None
db = None

def init_app():
    """Initialise l'application et le modèle IA"""
    global predictor, db
    
    try:
        db = get_db_connection()
        if not db.test_connection():
            print("ERREUR: Connexion base de donnees")
            return False
        
        print("OK: Connexion base de donnees")
        
        # Charger le modèle V2
        predictor = OlympicsAIPredictorV2()
        model_path = "models/trained/random_forest_model_v2.pkl"
        
        if os.path.exists(model_path):
            predictor.load_models(model_path)
            print("OK: Modele V2 charge")
        else:
            print("TRAINING: Entrainement du modele V2...")
            predictor.train_robust_models()
            predictor.save_models(model_path)
            print("OK: Modele V2 entraine et sauvegarde")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: Initialisation - {e}")
        return False

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/data')
def data():
    """Page données avec tableaux interactifs"""
    
    # Statistiques générales
    stats = {
        'athletes_2024': db.execute_query("SELECT COUNT(*) as count FROM paris2024_athletes WHERE sport != 'Unknown'").iloc[0]['count'],
        'countries': db.execute_query("SELECT COUNT(DISTINCT country) as count FROM paris2024_athletes").iloc[0]['count'],
        'sports': db.execute_query("SELECT COUNT(DISTINCT sport) as count FROM paris2024_athletes WHERE sport != 'Unknown'").iloc[0]['count'],
        'historical_games': db.execute_query("SELECT COUNT(DISTINCT game_slug) as count FROM olympic_results").iloc[0]['count']
    }
    
    # Top pays par nombre d'athlètes 2024
    top_countries = db.execute_query("""
        SELECT 
            country,
            COUNT(*) as athletes_count,
            COUNT(DISTINCT sport) as sports_count
        FROM paris2024_athletes 
        WHERE sport != 'Unknown'
        GROUP BY country
        ORDER BY athletes_count DESC
        LIMIT 15
    """)
    
    return render_template('data.html', stats=stats, top_countries=top_countries)

@app.route('/predictions')
def predictions():
    """Page prédictions avec modèle IA V2"""
    
    try:
        # Prédictions France
        france_results = predictor.predict_france_medals_realistic()
        
        # Prédictions Top 25 pays
        countries_results = predictor.predict_top25_countries_realistic()
        
        # Prédictions athlètes (échantillon)
        athletes_results = predictor.predict_individual_athletes_realistic()
        
        return render_template('predictions.html', 
                             france_results=france_results,
                             countries_results=countries_results[:15],
                             athletes_results=athletes_results[:20])
        
    except Exception as e:
        print(f"Erreur prédictions: {e}")
        return render_template('predictions.html', error=str(e))

@app.route('/visualizations')
def visualizations():
    """Page visualisations interactives"""
    return render_template('visualizations.html')

@app.route('/analysis')
def analysis():
    """Page analyse avancée"""
    return render_template('analysis.html')

@app.route('/api/data/countries')
def api_countries():
    """API données pays pour filtrage"""
    
    countries = db.execute_query("""
        SELECT DISTINCT country 
        FROM paris2024_athletes 
        WHERE sport != 'Unknown'
        ORDER BY country
    """)['country'].tolist()
    
    return jsonify(countries)

@app.route('/api/data/sports')
def api_sports():
    """API données sports pour filtrage"""
    
    sports = db.execute_query("""
        SELECT DISTINCT sport 
        FROM paris2024_athletes 
        WHERE sport != 'Unknown'
        ORDER BY sport
    """)['sport'].tolist()
    
    return jsonify(sports)

@app.route('/api/charts/athletes_by_country')
def api_chart_athletes_by_country():
    """Graphique: Athlètes par pays"""
    
    limit = request.args.get('limit', 15, type=int)
    
    data = db.execute_query(f"""
        SELECT 
            country,
            COUNT(*) as athletes_count
        FROM paris2024_athletes 
        WHERE sport != 'Unknown'
        GROUP BY country
        ORDER BY athletes_count DESC
        LIMIT {limit}
    """)
    
    fig = px.bar(
        data, 
        x='country', 
        y='athletes_count',
        title=f'Top {limit} Pays - Nombre d\'Athlètes Paris 2024',
        labels={'country': 'Pays', 'athletes_count': 'Nombre d\'Athlètes'},
        color='athletes_count',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=False
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/api/charts/sports_distribution')
def api_chart_sports_distribution():
    """Graphique: Distribution des sports"""
    
    data = db.execute_query("""
        SELECT 
            sport,
            COUNT(*) as athletes_count
        FROM paris2024_athletes 
        WHERE sport != 'Unknown'
        GROUP BY sport
        ORDER BY athletes_count DESC
        LIMIT 20
    """)
    
    fig = px.pie(
        data,
        values='athletes_count',
        names='sport',
        title='Distribution des Athlètes par Sport - Paris 2024'
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=600)
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/api/charts/predictions_france')
def api_chart_predictions_france():
    """Graphique: Prédictions France"""
    
    france_results = predictor.predict_france_medals_realistic()
    
    # Graphique en secteurs
    fig = go.Figure(data=[go.Pie(
        labels=['Or', 'Argent', 'Bronze'],
        values=[france_results['gold'], france_results['silver'], france_results['bronze']],
        hole=.3,
        marker_colors=['#FFD700', '#C0C0C0', '#CD7F32']
    )])
    
    fig.update_layout(
        title=f"Prédiction France - {france_results['total']} Médailles Totales",
        annotations=[dict(text=f"{france_results['total']}<br>Médailles", x=0.5, y=0.5, font_size=20, showarrow=False)],
        height=400
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/api/charts/predictions_countries')
def api_chart_predictions_countries():
    """Graphique: Prédictions top pays"""
    
    countries_results = predictor.predict_top25_countries_realistic()
    top_10 = countries_results[:10]
    
    countries = [c['country'] for c in top_10]
    medals = [c['predicted_total'] for c in top_10]
    
    fig = go.Figure(data=[
        go.Bar(x=countries, y=medals, marker_color='lightblue')
    ])
    
    fig.update_layout(
        title='Top 10 Pays - Prédictions Médailles Totales',
        xaxis_title='Pays',
        yaxis_title='Médailles Prédites',
        xaxis_tickangle=-45,
        height=500
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/api/charts/historical_france')
def api_chart_historical_france():
    """Graphique: Historique France vs Prédiction"""
    
    historical = db.execute_query("""
        SELECT 
            CAST(RIGHT(game_slug, 4) AS INTEGER) as year,
            COUNT(*) as total_medals
        FROM olympic_results 
        WHERE country_name = 'France'
        AND medal_type IN ('GOLD', 'SILVER', 'BRONZE')
        AND CAST(RIGHT(game_slug, 4) AS INTEGER) >= 2000
        GROUP BY CAST(RIGHT(game_slug, 4) AS INTEGER)
        ORDER BY year
    """)
    
    france_prediction = predictor.predict_france_medals_realistic()
    
    fig = go.Figure()
    
    # Données historiques
    fig.add_trace(go.Scatter(
        x=historical['year'],
        y=historical['total_medals'],
        mode='lines+markers',
        name='Historique',
        line=dict(color='blue')
    ))
    
    # Prédiction 2024
    fig.add_trace(go.Scatter(
        x=[2024],
        y=[france_prediction['total']],
        mode='markers',
        name='Prédiction 2024',
        marker=dict(color='red', size=12)
    ))
    
    fig.update_layout(
        title='France - Évolution Médailles (2000-2024)',
        xaxis_title='Année',
        yaxis_title='Nombre de Médailles',
        height=400
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/api/search/athletes')
def api_search_athletes():
    """API recherche d'athlètes avec filtres"""
    
    country = request.args.get('country', '')
    sport = request.args.get('sport', '')
    name = request.args.get('name', '')
    limit = request.args.get('limit', 50, type=int)
    
    query = """
        SELECT name, country, sport, age, date_of_birth
        FROM paris2024_athletes 
        WHERE sport != 'Unknown'
    """
    
    conditions = []
    if country:
        conditions.append(f"country = '{country}'")
    if sport:
        conditions.append(f"sport = '{sport}'")
    if name:
        conditions.append(f"name ILIKE '%{name}%'")
    
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    query += f" ORDER BY name LIMIT {limit}"
    
    athletes = db.execute_query(query)
    return jsonify(athletes.to_dict('records'))

if __name__ == '__main__':
    print("[START] Démarrage Webapp Neurolympics...")
    
    if init_app():
        print("[OK] Application initialisée avec succès")
        print("[WEB] Accès: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("[ERREUR] Échec initialisation application")