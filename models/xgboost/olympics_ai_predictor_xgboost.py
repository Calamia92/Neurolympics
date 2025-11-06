"""
MODELE IA XGBOOST V3 - ULTRA REALISTE
Utilise les résultats pré-calculés du notebook pour une webapp ultra-rapide

Interface compatible avec webapp Neurolympics
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pickle
from src.database.connection import get_db_connection


class OlympicsAIPredictorXGBoost:
    """Modèle IA XGBoost V3 - Utilise résultats pré-calculés"""

    def __init__(self):
        self.db = get_db_connection()
        self.precalculated_results = None
        self.is_loaded = False

    def load_models(self, filepath):
        """Charge les résultats pré-calculés depuis le notebook v3"""

        print(f"[XGBoost] Chargement des résultats pré-calculés...")

        # Charger les résultats pré-calculés
        results_path = os.path.join(
            os.path.dirname(filepath),
            'xgboost_predictions_v3.pkl'
        )

        try:
            if not os.path.exists(results_path):
                raise FileNotFoundError(f"Fichier résultats non trouvé: {results_path}")

            with open(results_path, 'rb') as f:
                self.precalculated_results = pickle.load(f)

            self.is_loaded = True

            metadata = self.precalculated_results.get('metadata', {})
            print(f"[XGBoost] ✅ Résultats chargés - Version: {metadata.get('version', 'v3')}")
            print(f"[XGBoost] ROC-AUC: {metadata.get('roc_auc', 'N/A')}")
            print(f"[XGBoost] Total médailles: {metadata.get('total_medals_predicted', 'N/A'):.1f}")
            print(f"[XGBoost] ⚡ Mode ultra-rapide activé!")

        except Exception as e:
            print(f"[XGBoost] ❌ Erreur chargement: {e}")
            print(f"[XGBoost] 💡 Exécutez le notebook v3_xgboost_prediction.ipynb pour générer les résultats")
            raise

    def predict_france_medals_realistic(self):
        """Q1: Prédiction France (résultats pré-calculés)"""

        if not self.is_loaded:
            raise ValueError("Modèle non chargé! Utilisez load_models() d'abord.")

        print("[XGBoost] === QUESTION 1: MEDAILLES FRANCE ===")

        result = self.precalculated_results['france']
        print(f"[XGBoost] FRANCE 2024: {result['gold']} Or, {result['silver']} Argent, {result['bronze']} Bronze")
        print(f"[XGBoost] TOTAL: {result['total']} médailles (sur {result['athletes_2024']} athlètes)")

        return result

    def predict_top25_countries_realistic(self):
        """Q2: Top 25 pays (résultats pré-calculés)"""

        if not self.is_loaded:
            raise ValueError("Modèle non chargé! Utilisez load_models() d'abord.")

        print("[XGBoost] === QUESTION 2: TOP 25 PAYS ===")

        predictions = self.precalculated_results['top25_countries']
        print("[XGBoost] TOP 5 PREDIT:")
        for pred in predictions[:5]:
            print(f"  {pred['rank']}. {pred['country']}: {pred['predicted_total']} médailles")

        return predictions

    def predict_individual_athletes_realistic(self):
        """Q3: Athlètes individuels (résultats pré-calculés)"""

        if not self.is_loaded:
            raise ValueError("Modèle non chargé! Utilisez load_models() d'abord.")

        print("[XGBoost] === QUESTION 3: ATHLETES INDIVIDUELS ===")

        results = self.precalculated_results['top_athletes']
        print("[XGBoost] TOP 10 ATHLETES PREDITS:")
        for i, athlete in enumerate(results[:10], 1):
            print(f"  {i}. {athlete['name']} ({athlete['country']}, {athlete['sport']}) - {athlete['medal_probability_pct']:.1f}%")

        return results

    def save_models(self, filepath):
        """Sauvegarde non implémentée (résultats générés dans notebook)"""
        print("[XGBoost] ⚠️  Exportez les résultats depuis le notebook v3_xgboost_prediction.ipynb")


def main():
    """Test du modèle XGBoost V3 avec résultats pré-calculés"""

    if not get_db_connection().test_connection():
        print("Erreur connexion base de données")
        return

    print("="*60)
    print("MODELE IA XGBOOST V3 - ULTRA REALISTE (MODE RAPIDE)")
    print("="*60)

    predictor = OlympicsAIPredictorXGBoost()

    try:
        # Charger les résultats pré-calculés
        model_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'trained',
            'xgboost_model.pkl'
        )

        predictor.load_models(model_path)

        # Prédictions (instantanées!)
        print("\n" + "="*60)

        france_result = predictor.predict_france_medals_realistic()
        top25_result = predictor.predict_top25_countries_realistic()
        athletes_result = predictor.predict_individual_athletes_realistic()

        print(f"\n{'='*60}")
        print("MODELE XGBOOST V3 TERMINE!")
        print(f"{'='*60}")

        return {
            'france': france_result,
            'top25': top25_result,
            'athletes': athletes_result
        }

    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = main()
