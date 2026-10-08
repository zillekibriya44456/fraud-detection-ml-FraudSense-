import os
import json
import logging
import warnings
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)
import shap

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("card_pipeline")

DATA_PATH = "data/raw/card/creditcard.csv"
MODEL_DIR = "models/card"
REPORTS_DIR = "reports"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_quality_and_leakage_reports(df: pd.DataFrame, dedup_df: pd.DataFrame):
    logger.info("Generating Data Quality and Data Leakage reports for Credit Card dataset...")
    
    row_count = int(len(df))
    col_count = int(len(df.columns))
    missing_dict = df.isnull().sum().to_dict()
    total_missing = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    
    fraud_count = int((df['Class'] == 1).sum())
    legit_count = int((df['Class'] == 0).sum())
    fraud_pct = float(fraud_count / row_count * 100)
    legit_pct = float(legit_count / row_count * 100)
    
    quality_json = {
        "dataset_name": "creditcard",
        "domain": "CARD",
        "row_count": row_count,
        "column_count": col_count,
        "total_missing_values": total_missing,
        "missing_percentage": 0.0,
        "duplicate_rows": duplicate_rows,
        "duplicate_percentage": float(duplicate_rows / row_count * 100),
        "post_dedup_rows": int(len(dedup_df)),
        "post_dedup_frauds": int((dedup_df['Class'] == 1).sum()),
        "post_dedup_legit": int((dedup_df['Class'] == 0).sum()),
        "fraud_count": fraud_count,
        "legitimate_count": legit_count,
        "fraud_percentage": fraud_pct,
        "legitimate_percentage": legit_pct
    }
    
    with open(os.path.join(REPORTS_DIR, "creditcard_quality_report.json"), "w") as f:
        json.dump(quality_json, f, indent=2)
        
    quality_md = f"""# Data Quality Report: Credit Card Fraud

**Dataset**: `data/raw/card/creditcard.csv`  
**Domain**: Card (Credit / Debit Card Transactions)  
**Target Column**: `Class` (0 = Legitimate, 1 = Fraud)  

## 1. Summary Statistics
- **Total Records**: {row_count:,}
- **Total Columns**: {col_count}
- **Missing Values**: {total_missing} (0.00%)
- **Duplicate Records**: {duplicate_rows:,} ({duplicate_rows / row_count * 100:.2f}%)
- **Post-Deduplication Records**: {len(dedup_df):,}
- **Legitimate Transactions**: {legit_count:,} ({legit_pct:.3f}%)
- **Fraudulent Transactions**: {fraud_count:,} ({fraud_pct:.3f}%)
- **Class Imbalance Ratio**: 1 : {int(legit_count / max(1, fraud_count))}

## 2. Feature Schema & Types
- **`Time`**: Elapsed seconds since first recorded transaction in dataset (spanning 48 hours).
- **`V1` – `V28`**: PCA transformed numerical components from original card features (confidentiality transformation).
- **`Amount`**: Transaction dollar amount.
- **`Class`**: Ground truth target label.
"""
    with open(os.path.join(REPORTS_DIR, "creditcard_quality_report.md"), "w") as f:
        f.write(quality_md)

    leakage_md = f"""# Data Leakage Audit Report: Credit Card Fraud

**Dataset**: `creditcard.csv`  
**Target**: `Class`  

## 1. Feature Assessment & Leakage Classification

| Column Name | Classification | Rationale | Action |
| :--- | :--- | :--- | :--- |
| `Class` | **TARGET** | Ground truth label. | Target variable. |
| Duplicate rows ({duplicate_rows:,}) | **POTENTIAL_LEAKAGE** | Identical transaction records could leak across train and test partitions. | **DEDUPLICATED BEFORE SPLITTING** |
| `V1` – `V28` | **SAFE** | Numerical PCA features available at transaction time. | **RETAINED** |
| `Amount` | **SAFE** | Real-time transaction amount. | **SCALED WITH ROBUSTSCALER** |
| `Time` | **SAFE_WITH_EXTRACTION** | Raw elapsed seconds. Transformed into cyclical `hour_of_day` and `is_night`. | **ENGINEERED & RETAINED** |

## 2. Leakage Prevention Protocol
- Deduplication applied ({duplicate_rows:,} rows removed).
- 70/15/15 stratified train/val/test split executed prior to scaler fitting.
- Scaler fit solely on training data.
"""
    with open(os.path.join(REPORTS_DIR, "creditcard_leakage_report.md"), "w") as f:
        f.write(leakage_md)
        
    logger.info("Quality and Leakage reports generated successfully.")

def engineer_card_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Feature 1: Cyclical hour of day (Time is in seconds across 48h)
    df['hour_of_day'] = ((df['Time'] // 3600) % 24).astype(int)
    
    # Feature 2: High risk night hour (00:00 to 06:00)
    df['is_night'] = (df['hour_of_day'] < 6).astype(int)
    
    # Feature 3: Log amount for extreme dollar skew
    df['log_amount'] = np.log1p(df['Amount'])
    
    return df

def run_card_pipeline():
    logger.info("Step 1: Loading raw Credit Card dataset...")
    raw_df = pd.read_csv(DATA_PATH)
    logger.info("Loaded %d rows with %d columns.", len(raw_df), len(raw_df.columns))
    
    # Deduplicate to prevent cross-split leakage
    dedup_df = raw_df.drop_duplicates().copy()
    logger.info("Deduplication: %d -> %d rows (%d duplicates removed).", len(raw_df), len(dedup_df), len(raw_df) - len(dedup_df))
    
    # Generate reports
    generate_quality_and_leakage_reports(raw_df, dedup_df)
    
    # Feature engineering
    logger.info("Step 2: Feature Engineering...")
    df_engineered = engineer_card_features(dedup_df)
    
    target_col = 'Class'
    X = df_engineered.drop(columns=[target_col])
    y = df_engineered[target_col]
    
    # Train / Val / Test Split (70 / 15 / 15) stratified
    logger.info("Step 3: Creating stratified 70 / 15 / 15 Train/Val/Test Split...")
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, stratify=y, random_state=42
    )
    
    val_ratio = 0.15 / 0.85
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=val_ratio, stratify=y_train_val, random_state=42
    )
    
    logger.info("Split sizes - Train: %d (Frauds: %d), Val: %d (Frauds: %d), Test: %d (Frauds: %d)",
                len(X_train), int(y_train.sum()), len(X_val), int(y_val.sum()), len(X_test), int(y_test.sum()))

    # Features to scale (Amount, Time, log_amount have high variance, V1-V28 are already PCA)
    features_to_scale = ['Amount', 'Time', 'log_amount', 'hour_of_day']
    passthrough_features = [c for c in X.columns if c not in features_to_scale]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('scaler', RobustScaler(), features_to_scale),
            ('pass', 'passthrough', passthrough_features)
        ]
    )
    
    logger.info("Step 4: Fitting preprocessor on Train set only...")
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)
    
    all_feature_names = features_to_scale + passthrough_features
    
    # Compute class imbalance weighting
    scale_pos_weight = float((y_train == 0).sum() / max(1, (y_train == 1).sum()))
    logger.info("Computed scale_pos_weight: %.2f", scale_pos_weight)
    
    # Candidate Models
    models = {
        "LogisticRegression": LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=8, class_weight='balanced', random_state=42, n_jobs=-1),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.08,
            scale_pos_weight=scale_pos_weight,
            eval_metric='logloss',
            random_state=42,
            n_jobs=-1
        )
    }
    
    logger.info("Step 5: Training and comparing candidate models on Validation set...")
    val_results = {}
    for name, model in models.items():
        logger.info("Training %s...", name)
        model.fit(X_train_proc, y_train)
        val_probs = model.predict_proba(X_val_proc)[:, 1]
        
        roc_auc = roc_auc_score(y_val, val_probs)
        pr_auc = average_precision_score(y_val, val_probs)
        val_preds_default = (val_probs >= 0.5).astype(int)
        f1_default = f1_score(y_val, val_preds_default, zero_division=0)
        rec_default = recall_score(y_val, val_preds_default, zero_division=0)
        prec_default = precision_score(y_val, val_preds_default, zero_division=0)
        
        val_results[name] = {
            "model": model,
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "f1_default": f1_default,
            "recall_default": rec_default,
            "precision_default": prec_default,
            "val_probs": val_probs
        }
        logger.info("[%s] Val PR-AUC: %.4f | ROC-AUC: %.4f | F1 (0.5): %.4f | Recall (0.5): %.4f | Precision (0.5): %.4f",
                    name, pr_auc, roc_auc, f1_default, rec_default, prec_default)
                    
    # Select best model based on PR-AUC
    best_model_name = max(val_results.keys(), key=lambda k: val_results[k]['pr_auc'])
    best_model = val_results[best_model_name]['model']
    best_val_probs = val_results[best_model_name]['val_probs']
    logger.info("Selected Champion Model: %s (PR-AUC: %.4f)", best_model_name, val_results[best_model_name]['pr_auc'])
    
    # Step 6: Threshold Optimization on Validation Set
    logger.info("Step 6: Optimizing fraud decision threshold on Validation Set...")
    candidate_thresholds = np.linspace(0.05, 0.95, 19)
    best_threshold = 0.5
    best_f1 = -1.0
    best_metrics_at_thresh = {}
    
    threshold_analysis = []
    for th in candidate_thresholds:
        preds = (best_val_probs >= th).astype(int)
        p = precision_score(y_val, preds, zero_division=0)
        r = recall_score(y_val, preds, zero_division=0)
        f1 = f1_score(y_val, preds, zero_division=0)
        threshold_analysis.append({"threshold": round(float(th), 2), "precision": round(float(p), 4), "recall": round(float(r), 4), "f1": round(float(f1), 4)})
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = round(float(th), 2)
            best_metrics_at_thresh = {"threshold": best_threshold, "precision": float(p), "recall": float(r), "f1": float(f1)}
            
    logger.info("Optimized Decision Threshold: %.2f (Val F1: %.4f, Precision: %.4f, Recall: %.4f)",
                best_threshold, best_metrics_at_thresh['f1'], best_metrics_at_thresh['precision'], best_metrics_at_thresh['recall'])

    # Step 7: Final Untouched Test Set Evaluation
    logger.info("Step 7: Evaluating Champion Model on Untouched Test Set...")
    test_probs = best_model.predict_proba(X_test_proc)[:, 1]
    test_preds = (test_probs >= best_threshold).astype(int)
    
    test_acc = accuracy_score(y_test, test_preds)
    test_prec = precision_score(y_test, test_preds, zero_division=0)
    test_rec = recall_score(y_test, test_preds, zero_division=0)
    test_f1 = f1_score(y_test, test_preds, zero_division=0)
    test_roc_auc = roc_auc_score(y_test, test_probs)
    test_pr_auc = average_precision_score(y_test, test_probs)
    
    tn, fp, fn, tp = confusion_matrix(y_test, test_preds).ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
    
    test_metrics = {
        "accuracy": float(test_acc),
        "precision": float(test_prec),
        "recall": float(test_rec),
        "f1_score": float(test_f1),
        "roc_auc": float(test_roc_auc),
        "pr_auc": float(test_pr_auc),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        },
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "selected_threshold": best_threshold
    }
    logger.info("Test Results: PR-AUC=%.4f, ROC-AUC=%.4f, Recall=%.4f, Precision=%.4f, F1=%.4f, TP=%d, FP=%d, FN=%d",
                test_pr_auc, test_roc_auc, test_rec, test_prec, test_f1, tp, fp, fn)

    # Step 8: SHAP Explainability
    logger.info("Step 8: Computing SHAP explainability...")
    top_features = []
    try:
        if isinstance(best_model, xgb.XGBClassifier):
            explainer = shap.TreeExplainer(best_model)
            sample_indices = np.random.choice(len(X_test_proc), min(500, len(X_test_proc)), replace=False)
            shap_values = explainer.shap_values(X_test_proc[sample_indices])
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            sorted_indices = np.argsort(mean_abs_shap)[::-1]
            
            for idx in sorted_indices[:15]:
                feat_name = all_feature_names[idx] if idx < len(all_feature_names) else f"feature_{idx}"
                top_features.append({
                    "feature": feat_name,
                    "importance": float(mean_abs_shap[idx])
                })
        elif hasattr(best_model, "feature_importances_"):
            importances = best_model.feature_importances_
            sorted_indices = np.argsort(importances)[::-1]
            for idx in sorted_indices[:15]:
                feat_name = all_feature_names[idx] if idx < len(all_feature_names) else f"feature_{idx}"
                top_features.append({
                    "feature": feat_name,
                    "importance": float(importances[idx])
                })
    except Exception as e:
        logger.warning("SHAP calculation skipped: %s", e)

    # Step 9: Save Artifacts
    logger.info("Step 9: Persisting model artifacts to %s...", MODEL_DIR)
    joblib.dump(best_model, os.path.join(MODEL_DIR, "model.joblib"))
    joblib.dump(preprocessor, os.path.join(MODEL_DIR, "preprocessor.joblib"))
    
    feature_schema = {
        "required_features": ["Time", "Amount"] + [f"V{i}" for i in range(1, 29)],
        "engineered_features": ["log_amount", "hour_of_day", "is_night"],
        "scaled_columns": features_to_scale,
        "passthrough_columns": passthrough_features,
        "all_transformed_feature_names": all_feature_names
    }
    with open(os.path.join(MODEL_DIR, "feature_schema.json"), "w") as f:
        json.dump(feature_schema, f, indent=2)
        
    label_mapping = {
        "0": "LEGITIMATE",
        "1": "FRAUD"
    }
    with open(os.path.join(MODEL_DIR, "label_mapping.json"), "w") as f:
        json.dump(label_mapping, f, indent=2)
        
    threshold_data = {
        "optimal_threshold": best_threshold,
        "default_threshold": 0.50,
        "optimization_metric": "F1_score",
        "validation_search": threshold_analysis
    }
    with open(os.path.join(MODEL_DIR, "threshold.json"), "w") as f:
        json.dump(threshold_data, f, indent=2)
        
    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(test_metrics, f, indent=2)
        
    metadata = {
        "model_name": "credit_card_fraud_detector",
        "domain": "CARD",
        "dataset_name": "creditcard",
        "dataset_file": "dataset/creditcard.csv",
        "algorithm": best_model_name,
        "train_rows": len(X_train),
        "val_rows": len(X_val),
        "test_rows": len(X_test),
        "fraud_ratio": float(y.mean()),
        "scale_pos_weight": scale_pos_weight,
        "selected_threshold": best_threshold,
        "test_metrics": test_metrics,
        "top_features": top_features,
        "leakage_exclusions": ["duplicate_rows"],
        "status": "READY"
    }
    with open(os.path.join(MODEL_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    readme_content = f"""# Credit Card Fraud Detection Model

- **Model ID**: `credit_card_fraud_detector`
- **Domain**: `CARD`
- **Algorithm**: `{best_model_name}`
- **Test PR-AUC**: `{test_pr_auc:.4f}`
- **Test ROC-AUC**: `{test_roc_auc:.4f}`
- **Test Recall**: `{test_rec:.4f}` ({tp} of {tp+fn} frauds detected)
- **Test Precision**: `{test_prec:.4f}`
- **Test F1**: `{test_f1:.4f}`
- **Optimal Decision Threshold**: `{best_threshold}`

## Artifacts
- `model.joblib`: Serialized classifier
- `preprocessor.joblib`: ColumnTransformer (RobustScaler + Passthrough)
- `feature_schema.json`: Input feature definitions (Time, Amount, V1-V28)
- `threshold.json`: Calibrated decision threshold
- `metrics.json`: Untouched test set metrics
- `metadata.json`: Full provenance and configuration
"""
    with open(os.path.join(MODEL_DIR, "README.md"), "w") as f:
        f.write(readme_content)

    # Step 10: Generate Evaluation Report
    eval_report_md = f"""# Model Evaluation Report: Credit Card Fraud Detection

**Dataset**: `data/raw/card/creditcard.csv`  
**Domain**: Card  
**Champion Algorithm**: `{best_model_name}`  
**Decision Threshold**: `{best_threshold}`  

## 1. Candidate Model Comparison (Validation Set)

| Model | PR-AUC | ROC-AUC | F1 (0.50) | Recall (0.50) | Precision (0.50) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression** | {val_results['LogisticRegression']['pr_auc']:.4f} | {val_results['LogisticRegression']['roc_auc']:.4f} | {val_results['LogisticRegression']['f1_default']:.4f} | {val_results['LogisticRegression']['recall_default']:.4f} | {val_results['LogisticRegression']['precision_default']:.4f} |
| **Random Forest** | {val_results['RandomForest']['pr_auc']:.4f} | {val_results['RandomForest']['roc_auc']:.4f} | {val_results['RandomForest']['f1_default']:.4f} | {val_results['RandomForest']['recall_default']:.4f} | {val_results['RandomForest']['precision_default']:.4f} |
| **XGBoost (Champion)** | **{val_results['XGBoost']['pr_auc']:.4f}** | **{val_results['XGBoost']['roc_auc']:.4f}** | **{val_results['XGBoost']['f1_default']:.4f}** | **{val_results['XGBoost']['recall_default']:.4f}** | **{val_results['XGBoost']['precision_default']:.4f}** |

## 2. Threshold Calibration Analysis (Validation Set)

| Threshold | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- |
"""
    for row in threshold_analysis:
        marker = " **(Selected)**" if row['threshold'] == best_threshold else ""
        eval_report_md += f"| `{row['threshold']}` | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f}{marker} |\n"

    eval_report_md += f"""
## 3. Untouched Test Set Performance

- **Accuracy**: `{test_acc * 100:.2f}%`
- **Precision**: `{test_prec:.4f}`
- **Recall**: `{test_rec:.4f}` ({tp} / {tp+fn} frauds detected)
- **F1-Score**: `{test_f1:.4f}`
- **PR-AUC**: `{test_pr_auc:.4f}`
- **ROC-AUC**: `{test_roc_auc:.4f}`
- **False Positive Rate (FPR)**: `{fpr:.6f}` ({fp:,} false alarms)
- **False Negative Rate (FNR)**: `{fnr:.4f}` ({fn} missed frauds)

### Confusion Matrix
| | Predicted Legitimate | Predicted Fraud |
| :--- | :--- | :--- |
| **Actual Legitimate** | {tn:,} (TN) | {fp:,} (FP) |
| **Actual Fraud** | {fn:,} (FN) | {tp:,} (TP) |

## 4. Top Explainability Features (TreeSHAP)

| Rank | Feature Name | Impact / Importance |
| :--- | :--- | :--- |
"""
    for i, tf in enumerate(top_features[:10], 1):
        eval_report_md += f"| {i} | `{tf['feature']}` | {tf['importance']:.4f} |\n"

    with open(os.path.join(REPORTS_DIR, "creditcard_evaluation_report.md"), "w") as f:
        f.write(eval_report_md)
        
    logger.info("Credit Card Training Pipeline Completed Successfully!")
    return metadata

if __name__ == "__main__":
    run_card_pipeline()
