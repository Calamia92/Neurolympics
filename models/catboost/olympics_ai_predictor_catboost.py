import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, mean_absolute_error, roc_auc_score, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV
from sklearn.base import BaseEstimator, ClassifierMixin
import joblib

from src.database.connection import get_db_connection


class SimpleCalibratedModel:
    """Top-level container combining a base estimator and a calibrator (logistic regressor).

    Implemented at module scope so it can be pickled when saving models.
    """
    def __init__(self, base, calibrator):
        self.base = base
        self.calibrator = calibrator

    def predict_proba(self, X):
        p = self.base.predict_proba(X)[:, 1]
        calibrated = self.calibrator.predict_proba(p.reshape(-1, 1))[:, 1]
        import numpy as _np
        return _np.vstack([1 - calibrated, calibrated]).T

    def predict(self, X):
        p = self.predict_proba(X)[:, 1]
        return (p >= 0.5).astype(int)


class CatBoostSklearnWrapper(BaseEstimator, ClassifierMixin):
    """Top-level sklearn-compatible wrapper around CatBoostClassifier.

    Implemented at module scope so instances can be pickled by joblib.
    The wrapper lazily imports CatBoostClassifier to avoid requiring catboost
    at module import time.
    """
    def __init__(self, cat_features=None, **params):
        # store init params so get_params works
        self._init_params = params.copy()
        # keep cat features as list of column names
        self.cat_features = list(cat_features) if cat_features is not None else []
        self.params = params.copy()
        self.model = None

    def _ensure_model(self):
        if self.model is None:
            # lazy import
            from catboost import CatBoostClassifier
            self.model = CatBoostClassifier(**self.params)

    def fit(self, X, y):
        self._ensure_model()
        # allow DataFrame input and pass categorical columns
        try:
            self.model.fit(X, y, cat_features=self.cat_features, verbose=False)
        except TypeError:
            # fallback if signature differs
            self.model.fit(X, y, verbose=False)
        # sklearn compatibility
        try:
            import numpy as _np
            self.classes_ = _np.unique(y)
        except Exception:
            self.classes_ = None
        try:
            self.n_features_in_ = X.shape[1]
        except Exception:
            pass
        return self

    def predict(self, X):
        self._ensure_model()
        return self.model.predict(X)

    def predict_proba(self, X):
        self._ensure_model()
        return self.model.predict_proba(X)

    def get_params(self, deep=True):
        # return the init params so sklearn.clone works
        return dict(self._init_params)

    def set_params(self, **params):
        # update init params and forward to underlying model if present
        self._init_params.update(params)
        self.params.update(params)
        if self.model is not None:
            try:
                self.model.set_params(**params)
            except Exception:
                pass
        return self


class EnsembleAveraging:
    """Picklable ensemble wrapper that averages predict_proba over a list of base estimators."""
    def __init__(self, models):
        self.models = list(models)

    def predict_proba(self, X):
        # Average predicted probabilities across models
        import numpy as _np
        probs = None
        for m in self.models:
            p = m.predict_proba(X)
            if probs is None:
                probs = p
            else:
                probs = probs + p
        probs = probs / float(len(self.models))
        return probs

    def predict(self, X):
        p = self.predict_proba(X)[:, 1]
        return (p >= 0.5).astype(int)


class OlympicsAIPredictorCatBoost:
    """Adaptateur CatBoost qui expose la même API que la version RandomForest V2."""

    def __init__(self):
        self.db = get_db_connection()
        self.athlete_model = None
        self.country_model = None
        self.label_encoders = {}
        self.is_trained = False

        self.realistic_stats = {
            'total_medals_per_olympics': 1000,
            'france_avg_medals': 37,
            'usa_avg_medals': 115,
            'top_countries_share': 0.6
        }

    # --- Data cleaning and feature builders reused from RF V2 ---
    def clean_training_data(self):
        # Include athletes with and without medals by starting from olympic_athletes
        # and left-joining olympic_results. This ensures we have negative examples
        # (has_medal = 0) for training the athlete classifier.
        athlete_query = """
        SELECT DISTINCT
            COALESCE(r.athlete_name, a.full_name) as athlete_name,
            r.country_name as country_name,
            COALESCE(r.discipline, '') as discipline,
            COALESCE(r.game_slug, '') as game_slug,
            CASE WHEN r.medal_type IN ('GOLD', 'SILVER', 'BRONZE') THEN 1 ELSE 0 END as has_medal,
            r.medal_type,
            CAST(RIGHT(COALESCE(r.game_slug, '2000'), 4) AS INTEGER) as game_year,
            a.birth_year,
            a.medals_count as career_medals,
            a.games_participations
        FROM olympic_athletes a
        LEFT JOIN olympic_results r ON a.athlete_url = r.athlete_url OR r.athlete_name = a.full_name
        WHERE COALESCE(r.athlete_name, a.full_name) IS NOT NULL
        AND LENGTH(COALESCE(r.athlete_name, a.full_name)) > 2
        """

        athlete_df = self.db.execute_query(athlete_query)
        athlete_df = athlete_df[athlete_df['game_year'] >= 2000]

        country_query = """
        SELECT 
            r.country_name,
            CAST(RIGHT(r.game_slug, 4) AS INTEGER) as game_year,
            COUNT(DISTINCT r.athlete_name) as total_athletes,
            SUM(CASE WHEN r.medal_type = 'GOLD' THEN 1 ELSE 0 END) as gold_medals,
            SUM(CASE WHEN r.medal_type = 'SILVER' THEN 1 ELSE 0 END) as silver_medals,
            SUM(CASE WHEN r.medal_type = 'BRONZE' THEN 1 ELSE 0 END) as bronze_medals,
            COUNT(DISTINCT r.discipline) as sports_count
        FROM olympic_results r
        WHERE r.country_name IS NOT NULL
        AND r.medal_type IN ('GOLD', 'SILVER', 'BRONZE', 'NA')
        GROUP BY r.country_name, CAST(RIGHT(r.game_slug, 4) AS INTEGER)
        HAVING COUNT(DISTINCT r.athlete_name) >= 5
        """

        country_df = self.db.execute_query(country_query)
        country_df = country_df[country_df['game_year'] >= 2000]
        country_df['total_medals'] = country_df['gold_medals'] + country_df['silver_medals'] + country_df['bronze_medals']

        return athlete_df, country_df

    def create_smart_athlete_features(self, athlete_df):
        """Create features for athletes and return X (DataFrame) and y (Series).

        For CatBoost we keep categorical columns as strings and pass them as cat_features.
        """
        features_df = athlete_df.copy()

        # Temporal features
        features_df['birth_year'] = features_df['birth_year'].fillna(1985)
        features_df['age_at_games'] = features_df['game_year'] - features_df['birth_year']
        features_df['age_at_games'] = features_df['age_at_games'].clip(15, 45)

        # Career features
        features_df['career_medals'] = features_df['career_medals'].fillna(0)
        features_df['games_participations'] = features_df['games_participations'].fillna(1)
        features_df['is_experienced'] = (features_df['games_participations'] > 1).astype(int)
        features_df['is_decorated'] = (features_df['career_medals'] > 0).astype(int)

        # Country / sport aggregated features
        country_performance = athlete_df.groupby('country_name').agg({
            'has_medal': 'mean',
            'career_medals': 'mean'
        }).round(4)
        country_performance.columns = ['country_medal_rate', 'country_avg_career_medals']
        features_df = features_df.merge(country_performance, on='country_name', how='left')
        features_df['country_medal_rate'] = features_df['country_medal_rate'].fillna(0.05)
        features_df['country_avg_career_medals'] = features_df['country_avg_career_medals'].fillna(0.1)

        sport_performance = athlete_df.groupby('discipline').agg({'has_medal': 'mean'}).round(4)
        sport_performance.columns = ['sport_medal_rate']
        features_df = features_df.merge(sport_performance, on='discipline', how='left')
        features_df['sport_medal_rate'] = features_df['sport_medal_rate'].fillna(0.1)

        optimal_ages = {'Swimming': 22, 'Athletics': 26, 'Gymnastics': 20, 'Cycling': 28, 'Wrestling': 27, 'Boxing': 25}
        features_df['age_deviation'] = features_df.apply(
            lambda x: abs(x['age_at_games'] - optimal_ages.get(x['discipline'], 25)), axis=1
        )

        # Keep categorical columns as-is for CatBoost
        self.athlete_features = [
            'country_name',
            'discipline',
            'age_at_games',
            'age_deviation',
            'career_medals',
            'games_participations',
            'is_experienced',
            'is_decorated',
            'country_medal_rate',
            'country_avg_career_medals',
            'sport_medal_rate'
        ]

        X = features_df[self.athlete_features].fillna(0)
        y = features_df['has_medal']
        return X, y

    def create_smart_country_features(self, country_df):
        features_df = country_df.copy()

        features_df['medal_rate'] = features_df['total_medals'] / features_df['total_athletes'].clip(1, None)
        features_df['athletes_per_sport'] = features_df['total_athletes'] / features_df['sports_count'].clip(1, None)
        features_df['medal_efficiency'] = features_df['total_medals'] / features_df['sports_count'].clip(1, None)

        country_historical = features_df.groupby('country_name').agg({'total_medals': ['mean', 'std'], 'total_athletes': 'mean', 'medal_rate': 'mean'}).round(3)
        country_historical.columns = ['avg_medals', 'std_medals', 'avg_athletes', 'avg_medal_rate']
        features_df = features_df.merge(country_historical, on='country_name', how='left')

        # Use country_name as categorical
        self.country_features = [
            'country_name',
            'total_athletes',
            'sports_count',
            'medal_rate',
            'athletes_per_sport',
            'medal_efficiency',
            'avg_medal_rate'
        ]

        X = features_df[self.country_features].fillna(0)
        y = features_df['total_medals']
        return X, y, features_df

    def train_robust_models(self):
        athlete_df, country_df = self.clean_training_data()
        X_athlete, y_athlete = self.create_smart_athlete_features(athlete_df)

        # Quick sanity check on labels
        try:
            vc = y_athlete.value_counts()
            print(f"Athlete label distribution:\n{vc.to_dict()}")
        except Exception:
            pass

        if (y_athlete == 0).sum() == 0:
            X_balanced = X_athlete
            y_balanced = y_athlete
        else:
            from sklearn.utils import resample
            df_majority = X_athlete[y_athlete == 0]
            df_minority = X_athlete[y_athlete == 1]
            df_majority_downsampled = resample(df_majority, replace=False, n_samples=len(df_minority) * 3, random_state=42)
            X_balanced = pd.concat([df_majority_downsampled, df_minority])
            y_balanced = pd.concat([pd.Series([0] * len(df_majority_downsampled)), pd.Series([1] * len(df_minority))])

        if len(y_balanced.unique()) > 1:
            X_train, X_test, y_train, y_test = train_test_split(X_balanced, y_balanced, test_size=0.2, random_state=42, stratify=y_balanced)
        else:
            X_train, X_test, y_train, y_test = train_test_split(X_balanced, y_balanced, test_size=0.2, random_state=42)
        # If after splitting the train labels contain only one class, skip athlete model training
        if len(y_train.unique()) <= 1:
            print("Warning: athlete training labels contain only one class after split. Skipping athlete model training.")
            self.athlete_model = None
            athlete_accuracy = None
        else:
            # Import CatBoost here (lazy import) so simply importing this module doesn't require CatBoost to be installed.
            from catboost import CatBoostClassifier, CatBoostRegressor

            # Build CatBoost model using native categorical support.
            # We'll wrap CatBoost in a small sklearn-compatible wrapper so CalibratedClassifierCV can be used.
            cat_features = ['country_name', 'discipline']

            # Use the top-level CatBoostSklearnWrapper (module-scope) so instances are picklable
            # For a quick test use fewer iterations and enable early stopping/eval_set and class weights
            # Class weights to handle imbalance: give more weight to positive class
            neg = int((y_train == 0).sum())
            pos = int((y_train == 1).sum())
            pos_weight = max(1.0, neg / max(1, pos))
            # CatBoost expects class_weights as list [w0, w1]
            class_weights = [1.0, float(pos_weight)]

            # V2: Stratified K-fold CatBoost ensemble with out-of-fold calibration
            from sklearn.model_selection import StratifiedKFold
            from sklearn.linear_model import LogisticRegression
            from catboost import Pool

            neg = int((y_train == 0).sum())
            pos = int((y_train == 1).sum())
            pos_weight = max(1.0, neg / max(1, pos))
            class_weights = [1.0, float(pos_weight)]

            n_splits = 5
            if pos < n_splits:
                n_splits = max(2, pos)

            skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            base_models = []
            oof_preds = np.zeros(len(X_train))
            X_train_arr = X_train.reset_index(drop=True)
            y_train_arr = y_train.reset_index(drop=True)

            cat_params = dict(iterations=300, depth=8, learning_rate=0.05, random_seed=42, class_weights=class_weights)

            for fold, (tr_idx, val_idx) in enumerate(skf.split(X_train_arr, y_train_arr)):
                X_tr = X_train_arr.iloc[tr_idx]
                y_tr = y_train_arr.iloc[tr_idx]
                X_val = X_train_arr.iloc[val_idx]
                y_val = y_train_arr.iloc[val_idx]

                clf = CatBoostSklearnWrapper(cat_features=cat_features, **cat_params)
                clf._ensure_model()
                try:
                    clf.model.fit(Pool(X_tr, y_tr, cat_features=cat_features), eval_set=Pool(X_val, y_val, cat_features=cat_features), early_stopping_rounds=50, use_best_model=True, verbose=False)
                except TypeError:
                    clf.model.fit(Pool(X_tr, y_tr, cat_features=cat_features), eval_set=Pool(X_val, y_val, cat_features=cat_features), early_stopping_rounds=50, use_best_model=True)

                base_models.append(clf)
                oof_preds[val_idx] = clf.predict_proba(X_val)[:, 1]

            # Train calibration on out-of-fold predictions
            lr = LogisticRegression(solver='lbfgs', max_iter=500)
            try:
                lr.fit(oof_preds.reshape(-1, 1), y_train_arr)
            except Exception:
                # fallback: train on a random split
                X_base_train, X_calib, y_base_train, y_calib = train_test_split(X_train, y_train, test_size=0.2, random_state=42, stratify=y_train)
                base_probs_calib = np.mean([m.predict_proba(X_calib)[:, 1] for m in base_models], axis=0)
                lr.fit(base_probs_calib.reshape(-1, 1), y_calib)

            ensemble = EnsembleAveraging(base_models)
            self.athlete_model = SimpleCalibratedModel(ensemble, lr)

            # Evaluate
            y_proba = self.athlete_model.predict_proba(X_test)[:, 1]
            y_pred = self.athlete_model.predict(X_test)
            athlete_accuracy = accuracy_score(y_test, y_pred)
            try:
                athlete_auc = roc_auc_score(y_test, y_proba)
            except Exception:
                athlete_auc = None
            try:
                athlete_brier = brier_score_loss(y_test, y_proba)
            except Exception:
                athlete_brier = None

            print(f"ATHLETE ENSEMBLE - acc: {athlete_accuracy:.4f}, AUC: {athlete_auc:.4f}, Brier: {athlete_brier:.4f} (n_models={len(base_models)})")

            # Report averaged feature importance across base models (if available)
            try:
                import numpy as _np
                fi = _np.mean([m.model.get_feature_importance(prettified=False) for m in base_models], axis=0)
                feat_names = X_train.columns.tolist()
                fi_pairs = sorted(zip(feat_names, fi), key=lambda x: x[1], reverse=True)[:10]
                print('Top features (avg importance):')
                for name, val in fi_pairs:
                    print(f"  {name}: {val:.2f}")
            except Exception:
                pass

        X_country, y_country, country_features_df = self.create_smart_country_features(country_df)
        X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X_country, y_country, test_size=0.2, random_state=42)

        # For country model, pass country_name as categorical feature
        # CatBoostRegressor can accept DataFrame with cat_features during fit
        # Ensure CatBoostRegressor is available (lazy import)
        try:
            from catboost import CatBoostRegressor
        except Exception:
            raise

        self.country_model = CatBoostRegressor(iterations=200, depth=8, learning_rate=0.1, random_seed=42)
        cat_feats_country = ['country_name']
        self.country_model.fit(X_train_c, y_train_c, cat_features=cat_feats_country, verbose=False)
        country_predictions = self.country_model.predict(X_test_c)
        country_mae = mean_absolute_error(y_test_c, country_predictions)

        self.is_trained = True
        return athlete_accuracy, country_mae

    def predict_france_medals_realistic(self):
        france_recent = self.db.execute_query("""
            SELECT 
                CAST(RIGHT(game_slug, 4) AS INTEGER) as year,
                SUM(CASE WHEN medal_type = 'GOLD' THEN 1 ELSE 0 END) as gold,
                SUM(CASE WHEN medal_type = 'SILVER' THEN 1 ELSE 0 END) as silver,
                SUM(CASE WHEN medal_type = 'BRONZE' THEN 1 ELSE 0 END) as bronze,
                COUNT(*) as total
            FROM olympic_results 
            WHERE country_name = 'France'
            AND medal_type IN ('GOLD', 'SILVER', 'BRONZE')
            AND CAST(RIGHT(game_slug, 4) AS INTEGER) >= 2000
            GROUP BY CAST(RIGHT(game_slug, 4) AS INTEGER)
            ORDER BY year DESC
        """)

        if not france_recent.empty:
            avg_medals = france_recent['total'].mean()
        else:
            avg_medals = self.realistic_stats.get('france_avg_medals', 37)

        host_factor = 1.15
        french_athletes = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM paris2024_athletes 
            WHERE country = 'France'
        """).iloc[0]['count']

        base_prediction = avg_medals
        predicted_total = int(base_prediction * host_factor)

        if not france_recent.empty:
            gold_ratio = france_recent['gold'].sum() / france_recent['total'].sum()
            silver_ratio = france_recent['silver'].sum() / france_recent['total'].sum()
            bronze_ratio = france_recent['bronze'].sum() / france_recent['total'].sum()
        else:
            gold_ratio, silver_ratio, bronze_ratio = 0.30, 0.33, 0.37

        predicted_gold = int(predicted_total * gold_ratio)
        predicted_silver = int(predicted_total * silver_ratio)
        predicted_bronze = predicted_total - predicted_gold - predicted_silver

        return {
            'gold': predicted_gold,
            'silver': predicted_silver,
            'bronze': predicted_bronze,
            'total': predicted_total,
            'athletes_2024': french_athletes,
            'method': 'Modele IA CatBoost (Realiste)'
        }

    def predict_top25_countries_realistic(self):
        countries_2024 = self.db.execute_query("""
            SELECT 
                country,
                COUNT(*) as athletes_2024,
                COUNT(DISTINCT sport) as sports_count
            FROM paris2024_athletes 
            WHERE sport != 'Unknown'
            GROUP BY country
            ORDER BY athletes_2024 DESC
        """)

        predictions = []
        total_predicted_medals = 0

        for _, country_data in countries_2024.iterrows():
            country = country_data['country']
            athletes = country_data['athletes_2024']
            sports = country_data['sports_count']

            historical = self.db.execute_query(f"""
                SELECT AVG(
                    CASE WHEN medal_type IN ('GOLD', 'SILVER', 'BRONZE') THEN 1 ELSE 0 END
                ) as medal_rate
                FROM olympic_results 
                WHERE country_name = '{country.replace("'", "''")}'
                AND CAST(RIGHT(game_slug, 4) AS INTEGER) >= 2000
            """)

            if not historical.empty and historical.iloc[0]['medal_rate'] is not None:
                historical_rate = float(historical.iloc[0]['medal_rate'])
            else:
                historical_rate = 0.05

            base_medals = athletes * historical_rate * 2.5
            country_factors = {
                'United States': 1.0,
                'China': 0.9,
                'France': 1.1,
                'Germany': 0.8,
                'Great Britain': 0.7,
                'Italy': 0.7,
                'Australia': 0.8,
                'Japan': 0.7,
                'Netherlands': 0.7,
                'Canada': 0.6
            }

            factor = country_factors.get(country, 0.4)
            predicted_medals = max(1, int(base_medals * factor))

            # Blend with country_model if available
            blend_weight = 0.35
            if self.country_model is not None:
                try:
                    row = {
                        'country_name': country,
                        'total_athletes': int(athletes),
                        'sports_count': int(sports),
                        'medal_rate': historical_rate,
                        'athletes_per_sport': athletes / max(1, int(sports)),
                        'medal_efficiency': predicted_medals / max(1, int(sports)),
                        'avg_medal_rate': historical_rate
                    }
                    X_row = pd.DataFrame([row])[self.country_features].fillna(0)
                    try:
                        model_medals = float(self.country_model.predict(X_row)[0])
                        predicted_medals = max(1, int((1 - blend_weight) * predicted_medals + blend_weight * model_medals))
                    except Exception:
                        pass
                except Exception:
                    pass

            predicted_gold = int(predicted_medals * 0.30)
            predicted_silver = int(predicted_medals * 0.33)
            predicted_bronze = predicted_medals - predicted_gold - predicted_silver

            predictions.append({
                'rank': len(predictions) + 1,
                'country': country,
                'predicted_total': predicted_medals,
                'predicted_gold': predicted_gold,
                'predicted_silver': predicted_silver,
                'predicted_bronze': predicted_bronze,
                'athletes_2024': athletes,
                'sports_count': sports
            })

            total_predicted_medals += predicted_medals

        target_total = 1000
        if total_predicted_medals > 0:
            normalization_factor = target_total / total_predicted_medals
            for pred in predictions:
                pred['predicted_total'] = max(1, int(pred['predicted_total'] * normalization_factor))
                pred['predicted_gold'] = int(pred['predicted_total'] * 0.30)
                pred['predicted_silver'] = int(pred['predicted_total'] * 0.33)
                pred['predicted_bronze'] = pred['predicted_total'] - pred['predicted_gold'] - pred['predicted_silver']

        predictions.sort(key=lambda x: x['predicted_total'], reverse=True)
        for i, pred in enumerate(predictions[:25]):
            pred['rank'] = i + 1

        return predictions[:25]

    def predict_individual_athletes_realistic(self):
        if not self.is_trained:
            raise ValueError("Modeles non entraines!")

        athletes_2024 = self.db.execute_query("""
            SELECT 
                name,
                country,
                sport as discipline,
                age,
                EXTRACT(YEAR FROM date_of_birth) as birth_year
            FROM paris2024_athletes 
            WHERE sport != 'Unknown'
            AND LENGTH(name) > 2
            ORDER BY RANDOM()
            LIMIT 2000
        """)

        features_df = athletes_2024.copy()
        # Align column names with training features: use country_name and discipline
        features_df['country_name'] = features_df['country']
        features_df['discipline'] = features_df['discipline']

        features_df['age_at_games'] = features_df['age'].fillna(25)
        features_df['age_deviation'] = abs(features_df['age_at_games'] - 25)
        features_df['career_medals'] = 0
        features_df['games_participations'] = 1
        features_df['is_experienced'] = 0
        features_df['is_decorated'] = 0
        features_df['country_medal_rate'] = 0.1
        features_df['country_avg_career_medals'] = 0.1
        features_df['sport_medal_rate'] = 0.15

        # Build feature matrix using same feature names as training
        X_features = features_df[self.athlete_features].fillna(0)

        # Predict probabilities (CatBoost wrapper accepts DataFrame)
        if self.athlete_model is None:
            # Fallback: model was not trained (single-class). Return small baseline probabilities.
            probabilities = np.full(len(X_features), 0.02)
        else:
            probabilities = self.athlete_model.predict_proba(X_features)[:, 1]

        # Debug: print whether model was used and mean predicted probability
        try:
            mean_p = float(np.mean(probabilities))
            if self.athlete_model is None:
                print(f"Athlete predictions: using fallback probabilities (mean={mean_p:.4f})")
            else:
                print(f"Athlete predictions: model used (mean probability={mean_p:.4f})")
        except Exception:
            pass

        results = []
        for i, (_, athlete) in enumerate(athletes_2024.iterrows()):
            results.append({
                'name': athlete['name'],
                'country': athlete['country'],
                'sport': athlete['discipline'],
                'medal_probability': float(probabilities[i]),
                'medal_probability_pct': float(probabilities[i] * 100)
            })

        results.sort(key=lambda x: x['medal_probability'], reverse=True)
        return results

    def save_models(self, filepath):
        model_data = {
            'athlete_model': self.athlete_model,
            'country_model': self.country_model,
            'label_encoders': self.label_encoders,
            'athlete_features': self.athlete_features,
            'country_features': self.country_features,
            'is_trained': self.is_trained,
            'version': 'CatBoost_V2'
        }
        # Ensure target directory exists and write atomically to avoid corrupting existing file on interruptions.
        dirpath = os.path.dirname(filepath)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        tmp_path = filepath + '.tmp'
        joblib.dump(model_data, tmp_path)
        try:
            # os.replace is atomic on most platforms
            os.replace(tmp_path, filepath)
        except Exception:
            # Fallback: try os.rename
            try:
                os.rename(tmp_path, filepath)
            except Exception:
                # If move fails, remove tmp and raise
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                raise
        # Confirm save location
        try:
            print(f"Saved model to: {os.path.abspath(filepath)} (version={model_data.get('version')})")
        except Exception:
            pass

    def load_models(self, filepath):
        try:
            model_data = joblib.load(filepath)
            print(f"Loaded model file: {os.path.abspath(filepath)}")
        except EOFError:
            # Rename corrupted file so the user can inspect it and avoid reloading
            corrupt_path = filepath + '.corrupt'
            try:
                os.replace(filepath, corrupt_path)
            except Exception:
                try:
                    os.rename(filepath, corrupt_path)
                except Exception:
                    pass
            raise RuntimeError(f"Model file appears corrupted and was moved to {corrupt_path}. Please retrain the model.")
        except Exception as e:
            # Other exceptions - re-raise with context
            raise RuntimeError(f"Failed to load model file {filepath}: {e}") from e

        self.athlete_model = model_data['athlete_model']
        self.country_model = model_data['country_model']
        self.label_encoders = model_data.get('label_encoders', {})
        self.athlete_features = model_data.get('athlete_features')
        self.country_features = model_data.get('country_features')
        self.is_trained = bool(model_data.get('is_trained', False))


def main():
    if not get_db_connection().test_connection():
        print("Erreur connexion base de donnees")
        return

    predictor = OlympicsAIPredictorCatBoost()
    print('Starting CatBoost training test...')
    predictor.train_robust_models()

    print(predictor.predict_france_medals_realistic())


if __name__ == '__main__':
    main()
