"""
Module de connexion à la base de données PostgreSQL AlwaysData
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import psycopg2

# Charger les variables d'environnement
load_dotenv()

class DatabaseConnection:
    def __init__(self):
        """Initialise la connexion à la base de données"""
        self.engine = None
        self.connection_string = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Configure la chaîne de connexion"""
        # Option 1: Utiliser l'URL complète
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            self.connection_string = database_url
        else:
            # Option 2: Construire l'URL à partir des composants
            host = os.getenv('DB_HOST')
            port = os.getenv('DB_PORT', '5432')
            database = os.getenv('DB_NAME')
            username = os.getenv('DB_USER')
            password = os.getenv('DB_PASSWORD')
            
            self.connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        # Afficher l'URL de connexion (sans le mot de passe)
        safe_url = self.connection_string.replace(os.getenv('DB_PASSWORD', ''), '*****')
        print(f"URL de connexion : {safe_url}")
        
        # Créer l'engine SQLAlchemy
        self.engine = create_engine(self.connection_string)
    
    def test_connection(self):
        """Teste la connexion à la base de données"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("OK - Connexion à la base de données réussie !")
                return True
        except Exception as e:
            print(f"ERREUR - Erreur de connexion : {e}")
            return False
    
    def execute_query(self, query, params=None):
        """Exécute une requête SQL et retourne un DataFrame"""
        try:
            df = pd.read_sql_query(query, self.engine, params=params)
            return df
        except Exception as e:
            print(f"ERREUR - Erreur lors de l'exécution de la requête : {e}")
            return None
    
    def get_tables(self):
        """Récupère la liste des tables disponibles"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        return self.execute_query(query)
    
    def insert_dataframe(self, df, table_name, if_exists='replace'):
        """Insère un DataFrame dans une table"""
        try:
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
            print(f"OK - Données insérées dans la table '{table_name}' avec succès !")
            return True
        except Exception as e:
            print(f"ERREUR - Erreur lors de l'insertion : {e}")
            return False

# Fonctions utilitaires
def get_db_connection():
    """Retourne une instance de connexion à la base de données"""
    return DatabaseConnection()

def load_olympic_data_to_db(db_conn, df_athletes, df_hosts, df_medals, df_results):
    """Charge tous les datasets olympiques dans la base de données"""
    tables = {
        'athletes': df_athletes,
        'hosts': df_hosts, 
        'medals': df_medals,
        'results': df_results
    }
    
    for table_name, df in tables.items():
        if df is not None and not df.empty:
            success = db_conn.insert_dataframe(df, f'olympic_{table_name}')
            if success:
                print(f"OK - Table 'olympic_{table_name}' créée avec {len(df)} lignes")
        else:
            print(f"ATTENTION - Dataset '{table_name}' vide ou invalide")

# Exemple d'utilisation
if __name__ == "__main__":
    # Test de connexion
    db = get_db_connection()
    db.test_connection()
    
    # Lister les tables
    tables = db.get_tables()
    print("Tables disponibles :")
    print(tables)