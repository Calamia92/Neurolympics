import os
import json
from models.catboost.olympics_ai_predictor_catboost import OlympicsAIPredictorCatBoost
import numpy as np

OUTPUT_JSON = 'outputs/catboost_results.json'
MODEL_PATH = 'models/trained/catboost_model_v1.pkl'

os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)

if __name__ == '__main__':
    print('Starting CatBoost full run...')
    predictor = OlympicsAIPredictorCatBoost()

    if os.path.exists(MODEL_PATH):
        print(f'Loading existing model: {MODEL_PATH}')
        predictor.load_models(MODEL_PATH)
    else:
        print('No trained model found. Training now...')
        acc, mae = predictor.train_robust_models()
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        predictor.save_models(MODEL_PATH)
        if acc is None:
            print(f'Training done. Athlete model skipped (single-class). MAE pays: {mae:.4f} -> saved to {MODEL_PATH}')
        else:
            print(f'Training done. accuracy={acc:.4f}, mae={mae:.4f} -> saved to {MODEL_PATH}')

    print('Running predictions...')
    france = predictor.predict_france_medals_realistic()
    top25 = predictor.predict_top25_countries_realistic()
    athletes = predictor.predict_individual_athletes_realistic()

    # Trim athlete list to top 50 for JSON size
    athletes_top = athletes[:50]

    out = {
        'france': france,
        'top25': top25,
        'athletes_top50': athletes_top
    }

    # Ensure numpy types are converted
    def convert(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        return o

    # Use json.dump with default conversion
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, default=convert, ensure_ascii=False, indent=2)

    print(f'Results saved to {OUTPUT_JSON}')
