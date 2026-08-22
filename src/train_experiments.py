import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.features.full_features import engineer_full_features
from src.features.realtime_features import engineer_realtime_features
from src.preprocessing import preprocess_and_split

def compute_metrics(y_true, y_pred, y_prob, latency_ms=0):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return {
        "precision": float(precision_score(y_true, y_pred)),
        "recall": float(recall_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "pr_auc": float(average_precision_score(y_true, y_prob)),
        "fpr": float(fp / (fp + tn)),
        "fnr": float(fn / (fn + tp)),
        "inference_latency_ms": latency_ms
    }

def train_and_evaluate(X_train, y_train, X_test, y_test, model_name, model_obj):
    print(f"Training {model_name}...")
    model_obj.fit(X_train, y_train)
    
    start_time = time.time()
    y_prob = model_obj.predict_proba(X_test)[:, 1]
    y_pred = model_obj.predict(X_test)
    end_time = time.time()
    
    # Calculate latency per sample in ms
    latency_ms = ((end_time - start_time) / len(X_test)) * 1000
    
    return compute_metrics(y_test, y_pred, y_prob, latency_ms), model_obj

def run_experiment():
    print("Loading dataset...")
    df = pd.read_csv('data/raw/PS_20174392719_1491204439457_log.csv')
    # Subsample to 500k rows for realistic comparison time
    fraud_df = df[df['isFraud'] == 1]
    legit_df = df[df['isFraud'] == 0].sample(n=min(len(df[df['isFraud'] == 0]), 500000), random_state=42)
    df = pd.concat([fraud_df, legit_df]).sample(frac=1, random_state=42).reset_index(drop=True)
    
    results = {}
    models_to_test = {
        "LogisticRegression": LogisticRegression(class_weight='balanced', max_iter=1000),
        "RandomForest": RandomForestClassifier(n_estimators=50, class_weight='balanced', n_jobs=-1, max_depth=10),
        "XGBoost": xgb.XGBClassifier(scale_pos_weight=(len(df)-df['isFraud'].sum())/df['isFraud'].sum(), n_jobs=-1)
    }
    
    # EXPERIMENT A: FULL FEATURE MODEL (Baseline)
    print("--- EXPERIMENT A: FULL FEATURE MODEL ---")
    df_full = engineer_full_features(df)
    
    # Drop string high-cardinality columns
    cols_to_drop = ['nameOrig', 'nameDest', 'isFlaggedFraud']
    df_full = df_full.drop(columns=[col for col in cols_to_drop if col in df_full.columns])
    
    X_train_f, X_val_f, X_test_f, y_train_f, y_val_f, y_test_f, preprocessor_f = preprocess_and_split(df_full)
    
    results['full_feature'] = {}
    for name, model in models_to_test.items():
        metrics, trained_model = train_and_evaluate(X_train_f, y_train_f, X_test_f, y_test_f, name, model)
        results['full_feature'][name] = metrics
        if name == "XGBoost":
            joblib.dump(preprocessor_f, 'models/full_feature/preprocessor.joblib')
            trained_model.save_model('models/full_feature/xgboost_fraud_model.json')
    
    # EXPERIMENT B: PRE-AUTHORIZATION MODEL (Real-Time Safe)
    print("--- EXPERIMENT B: PRE-AUTHORIZATION MODEL ---")
    df_real = engineer_realtime_features(df)
    # Exclude post-transaction columns explicitly before preprocessing
    cols_to_drop = ['newbalanceOrig', 'newbalanceDest', 'nameOrig', 'nameDest', 'isFlaggedFraud']
    df_real = df_real.drop(columns=[c for c in cols_to_drop if c in df_real.columns])
    
    X_train_r, X_val_r, X_test_r, y_train_r, y_val_r, y_test_r, preprocessor_r = preprocess_and_split(df_real)
    
    results['pre_authorization'] = {}
    for name, model in models_to_test.items():
        # Using the same model configurations
        metrics, trained_model = train_and_evaluate(X_train_r, y_train_r, X_test_r, y_test_r, name, model)
        results['pre_authorization'][name] = metrics
        if name == "XGBoost":
            joblib.dump(preprocessor_r, 'models/pre_authorization/preprocessor.joblib')
            trained_model.save_model('models/pre_authorization/xgboost_fraud_model.json')
            
    # Save results
    os.makedirs('artifacts/metrics', exist_ok=True)
    with open('artifacts/metrics/model_comparison.json', 'w') as f:
        json.dump(results, f, indent=4)
        
    print("Experiments completed. Metrics saved.")

if __name__ == "__main__":
    run_experiment()
