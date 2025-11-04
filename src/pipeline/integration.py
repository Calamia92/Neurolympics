"""
Pipeline d'intégration complète des données olympiques
Utilise le transformer et la connexion DB pour charger les données normalisées
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.processing.transformer import OlympicDataTransformer
from src.database.connection import get_db_connection
from src.processing.validator import SimpleDataValidator
import pandas as pd

def create_database_tables(db_conn, schema):
    """Crée les tables dans la base de données selon le schéma unifié"""
    print("=== Creation des tables ===")
    
    # Mapping des types Python vers PostgreSQL
    type_mapping = {
        'varchar': 'VARCHAR(255)',
        'varchar(255)': 'VARCHAR(255)',
        'varchar(100)': 'VARCHAR(100)',
        'varchar(50)': 'VARCHAR(50)',
        'varchar(20)': 'VARCHAR(20)',
        'varchar(10)': 'VARCHAR(10)',
        'text': 'TEXT',
        'integer': 'INTEGER',
        'date': 'DATE',
        'boolean': 'BOOLEAN'
    }
    
    for table_name, columns in schema.items():
        try:
            # Construire la requête CREATE TABLE
            column_definitions = []
            for col_name, col_type in columns.items():
                pg_type = type_mapping.get(col_type, 'TEXT')
                
                # Ajouter des contraintes spéciales
                if col_name.endswith('_id'):
                    column_definitions.append(f"{col_name} {pg_type} PRIMARY KEY")
                else:
                    column_definitions.append(f"{col_name} {pg_type}")
            
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS olympic_{table_name} (
                {', '.join(column_definitions)}
            );
            """
            
            # Exécuter la requête
            with db_conn.engine.connect() as conn:
                conn.execute(create_sql)
                conn.commit()
            
            print(f"OK Table 'olympic_{table_name}' creee")
            
        except Exception as e:
            print(f"ERREUR creation table '{table_name}': {e}")

def load_transformed_data(db_conn, datasets):
    """Charge les données transformées dans la base de données"""
    print("\n=== Chargement des donnees ===")
    
    for table_name, df in datasets.items():
        if df.empty:
            print(f"WARNING Dataset '{table_name}' vide, ignore")
            continue
            
        try:
            # Nettoyer les données avant insertion
            df_clean = clean_dataframe_for_db(df)
            
            # Insérer dans la base
            success = db_conn.insert_dataframe(df_clean, f'olympic_{table_name}', if_exists='replace')
            
            if success:
                print(f"OK {len(df_clean)} lignes inserees dans 'olympic_{table_name}'")
            else:
                print(f"ERREUR Echec insertion '{table_name}'")
                
        except Exception as e:
            print(f"ERREUR chargement '{table_name}': {e}")

def clean_dataframe_for_db(df):
    """Nettoie un DataFrame pour l'insertion en base"""
    df_clean = df.copy()
    
    # Remplacer les valeurs None/NaN par des valeurs appropriées
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            df_clean[col] = df_clean[col].fillna('')
        elif df_clean[col].dtype in ['int64', 'float64']:
            df_clean[col] = df_clean[col].fillna(0)
    
    # Limiter la longueur des chaînes si nécessaire
    for col in df_clean.select_dtypes(include=['object']).columns:
        if 'url' not in col.lower() and 'bio' not in col.lower():
            df_clean[col] = df_clean[col].astype(str).str[:255]
    
    return df_clean

def run_data_quality_checks(db_conn):
    """Exécute des vérifications de qualité des données"""
    print("\n=== Verifications qualite ===")
    
    checks = [
        ("Nombre total d'athlètes", "SELECT COUNT(*) FROM olympic_athletes"),
        ("Nombre de jeux olympiques", "SELECT COUNT(DISTINCT game_slug) FROM olympic_hosts"),
        ("Médailles par type", "SELECT medal_type, COUNT(*) FROM olympic_medals GROUP BY medal_type"),
        ("Pays avec le plus de médailles", """
            SELECT country_name, COUNT(*) as medal_count 
            FROM olympic_medals 
            GROUP BY country_name 
            ORDER BY medal_count DESC 
            LIMIT 5
        """)
    ]
    
    for check_name, query in checks:
        try:
            result = db_conn.execute_query(query)
            print(f"OK {check_name}:")
            print(result.to_string(index=False))
            print()
        except Exception as e:
            print(f"ERREUR verification '{check_name}': {e}")

def main():
    """Pipeline principal d'intégration"""
    print("PIPELINE D'INTEGRATION DONNEES OLYMPIQUES")
    print("=" * 50)
    
    # 1. Initialiser les composants
    validator = SimpleDataValidator()
    transformer = OlympicDataTransformer()
    db_conn = get_db_connection()
    
    # 2. VALIDATION PREALABLE DES DONNEES
    print("\nETAPE 1: VALIDATION DES DONNEES")
    print("-" * 30)
    validation_results = validator.check_all_files()
    validator.generate_summary(validation_results)
    
    # Verifier si on peut continuer
    error_files = sum(1 for r in validation_results.values() if r.get('status') == 'ERROR')
    if error_files > 0:
        print("\nARRET: Fichiers avec erreurs detectes. Correction manuelle requise.")
        return
    
    warning_files = sum(1 for r in validation_results.values() if r.get('status') == 'WARNING')
    if warning_files > 0:
        print("\nCONTINUATION: Nettoyage automatique des donnees...")
    
    # 3. Tester la connexion DB
    print("\nETAPE 2: CONNEXION BASE DE DONNEES")
    print("-" * 30)
    if not db_conn.test_connection():
        print("ERREUR: Impossible de se connecter a la base de donnees")
        return
    
    # 4. Transformer les datasets
    print("\nETAPE 3: TRANSFORMATION DES DONNEES")
    print("-" * 30)
    datasets = transformer.transform_all_datasets()
    
    # 5. Créer le schéma unifié
    print("\nETAPE 4: CREATION DU SCHEMA")
    print("-" * 30)
    schema = transformer.create_unified_schema()
    create_database_tables(db_conn, schema)
    
    # 6. Charger les données
    print("\nETAPE 5: CHARGEMENT DES DONNEES")
    print("-" * 30)
    load_transformed_data(db_conn, datasets)
    
    # 7. Vérifications qualité
    print("\nETAPE 6: VERIFICATIONS FINALES")
    print("-" * 30)
    run_data_quality_checks(db_conn)
    
    print("\nPIPELINE TERMINE AVEC SUCCES!")
    print("\nTables creees:")
    tables = db_conn.get_tables()
    if tables is not None and not tables.empty:
        for table in tables['table_name']:
            if table.startswith('olympic_'):
                print(f"  - {table}")
    else:
        print("  Aucune table trouvee")

if __name__ == "__main__":
    main()