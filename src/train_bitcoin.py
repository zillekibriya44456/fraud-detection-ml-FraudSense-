"""
Bitcoin Illicit Transaction Detection Training Pipeline
=========================================================
Dataset: Elliptic Bitcoin Dataset
  - Classes: '1' = illicit (fraud), '2' = licit (legitimate), 'unknown' = unlabelled
  - Features: 166 numerical features (94 local, 72 aggregated from neighbors)
  - Splitting: Temporal split based on time steps (1 to 49)

Pipeline:
  1. Load classes and features, merge on txId.
  2. Filter out 'unknown' classes.
  3. Map '1' -> 1 (FRAUD), '2' -> 0 (LEGITIMATE).
  4. Train/Val/Test Temporal Split (Train: steps 1-34, Val: 35-42, Test: 43-49).
  5. Train LR, RandomForest, XGBoost - compare on Val PR-AUC.
  6. Calibrate threshold on Val set.
  7. Final evaluation on Test set.
  8. SHAP Explainability.
  9. Persist artifacts to models/bitcoin/
"""
import os
import json
import logging
import warnings
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)
import shap

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("bitcoin_pipeline")

DATA_DIR = "dataset/elliptic_bitcoin_dataset"
CLASSES_PATH = os.path.join(DATA_DIR, "elliptic_txs_classes.csv")
FEATURES_PATH = os.path.join(DATA_DIR, "elliptic_txs_features.csv")
MODEL_DIR = "models/bitcoin"
REPORTS_DIR = "reports"
TARGET_COL = "fraud_flag"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def generate_reports(df: pd.DataFrame, total_rows_orig: int):
    logger.info("Generating Data Quality and Leakage reports...")

    row_count = int(len(df))
    col_count = int(len(df.columns))
    fraud_count = int((df[TARGET_COL] == 1).sum())
    legit_count = int((df[TARGET_COL] == 0).sum())
    fraud_pct = float(fraud_count / row_count * 100)

    quality_json = {
        "dataset_name": "elliptic_bitcoin",
        "domain": "CRYPTO_BITCOIN",
        "total_rows_with_unknowns": total_rows_orig,
        "labeled_rows": row_count,
        "feature_count": col_count - 3, # excluding txId, time_step, target
        "fraud_count": fraud_count,
        "legitimate_count": legit_count,
        "fraud_percentage": fraud_pct,
        "splitting_strategy": "Temporal (time_step)",
    }
    with open(os.path.join(REPORTS_DIR, "bitcoin_quality_report.json"), "w") as f:
        json.dump(quality_json, f, indent=2)

    quality_md = f"""# Data Quality Report: Elliptic Bitcoin Dataset

**Dataset**: `elliptic_bitcoin_dataset`
**Domain**: Cryptocurrency (Bitcoin)
**Target Column**: `fraud_flag` (Derived from class '1')

## 1. Summary Statistics
- **Total Labeled Records**: {row_count:,} (Filtered out 'unknown' classes)
- **Features**: {col_count - 3} (94 local, 72 aggregated)
- **Illicit Transactions (Fraud)**: {fraud_count:,} ({fraud_pct:.2f}%)
- **Licit Transactions (Legit)**: {legit_count:,} ({100 - fraud_pct:.2f}%)
- **Class Imbalance**: 1 : {int(legit_count / max(1, fraud_count))}
"""
    with open(os.path.join(REPORTS_DIR, "bitcoin_quality_report.md"), "w") as f:
        f.write(quality_md)

    leakage_md = """# Data Leakage Audit: Elliptic Bitcoin Dataset

**Dataset**: `elliptic_txs_features.csv`
**Target**: `fraud_flag`

## Feature Assessment
- The dataset contains 166 anonymized numerical features.
- First 94 features are local information (transaction inputs/outputs, fee, size, etc.).
- Remaining 72 features are aggregated network information from 1-hop backward/forward neighbors.
- `txId` is dropped to prevent memorization.
- `time_step` (1 to 49) represents ~2 weeks of transactions each.

## Leakage Prevention Protocol
- **Temporal Splitting**: To avoid future leakage, data is split chronologically:
  - Train: Steps 1 to 34
  - Validation: Steps 35 to 42
  - Test: Steps 43 to 49
- Features are scaled strictly using training data statistics.
"""
    with open(os.path.join(REPORTS_DIR, "bitcoin_leakage_report.md"), "w") as f:
        f.write(leakage_md)


def run_bitcoin_pipeline():
    logger.info("Step 1: Loading Bitcoin dataset...")
    df_classes = pd.read_csv(CLASSES_PATH)
    total_rows = len(df_classes)
    
    # Load features
    # Columns: [0: txId, 1: time_step, 2-167: features]
    df_features = pd.read_csv(FEATURES_PATH, header=None)
    feature_cols = [f"feature_{i}" for i in range(1, 166)]
    df_features.columns = ["txId", "time_step"] + feature_cols
    
    # Merge
    df = pd.merge(df_classes, df_features, on="txId", how="inner")
    
    # Filter knowns
    df_labeled = df[df['class'] != 'unknown'].copy()
    
    # Map target: '1' -> 1 (fraud), '2' -> 0 (legit)
    df_labeled[TARGET_COL] = df_labeled['class'].map({'1': 1, '2': 0})
    df_labeled = df_labeled.drop(columns=['class'])
    
    logger.info("Total labeled records: %d", len(df_labeled))
    
    generate_reports(df_labeled, total_rows)

    # ── 3. TEMPORAL SPLIT ────────────────────────────────────
    logger.info("Step 2: Temporal Train/Val/Test Split...")
    
    train_mask = df_labeled['time_step'] <= 34
    val_mask = (df_labeled['time_step'] > 34) & (df_labeled['time_step'] <= 42)
    test_mask = df_labeled['time_step'] > 42
    
    train_df = df_labeled[train_mask]
    val_df = df_labeled[val_mask]
    test_df = df_labeled[test_mask]
    
    drop_cols = ["txId", "time_step", TARGET_COL]
    
    X_train = train_df.drop(columns=drop_cols)
    y_train = train_df[TARGET_COL]
    
    X_val = val_df.drop(columns=drop_cols)
    y_val = val_df[TARGET_COL]
    
    X_test = test_df.drop(columns=drop_cols)
    y_test = test_df[TARGET_COL]
    
    logger.info("Train: %d (fraud: %d) | Val: %d (fraud: %d) | Test: %d (fraud: %d)",
                len(X_train), int(y_train.sum()),
                len(X_val), int(y_val.sum()),
                len(X_test), int(y_test.sum()))

    # ── 4. PREPROCESSING ─────────────────────────────────────
    logger.info("Step 3: Fitting scaler on Train set only...")
    numeric_cols = list(X_train.columns)
    
    preprocessor = ColumnTransformer([
        ('num', StandardScaler(), numeric_cols)
    ])
    
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)
    
    all_feature_names = numeric_cols
    
    scale_pos_weight = float((y_train == 0).sum() / max(1, (y_train == 1).sum()))
    logger.info("scale_pos_weight: %.2f", scale_pos_weight)

    # ── 5. TRAIN MODELS ──────────────────────────────────────
    models = {
        "LogisticRegression": LogisticRegression(
            class_weight='balanced', max_iter=1000, random_state=42
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=15, min_samples_leaf=2,
            class_weight='balanced', random_state=42, n_jobs=-1
        ),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            eval_metric='aucpr',
            tree_method='hist',
            random_state=42,
            n_jobs=-1
        ),
    }

    logger.info("Step 4: Training candidate models...")
    val_results = {}
    for name, model in models.items():
        logger.info("Training %s...", name)
        model.fit(X_train_proc, y_train)
        val_probs = model.predict_proba(X_val_proc)[:, 1]

        roc_auc = roc_auc_score(y_val, val_probs)
        pr_auc = average_precision_score(y_val, val_probs)
        val_preds = (val_probs >= 0.5).astype(int)
        f1 = f1_score(y_val, val_preds, zero_division=0)
        rec = recall_score(y_val, val_preds, zero_division=0)
        prec = precision_score(y_val, val_preds, zero_division=0)

        val_results[name] = {
            "model": model, "roc_auc": roc_auc, "pr_auc": pr_auc,
            "f1_default": f1, "recall_default": rec, "precision_default": prec,
            "val_probs": val_probs
        }
        logger.info("[%s] Val PR-AUC: %.4f | ROC-AUC: %.4f", name, pr_auc, roc_auc)

    best_name = max(val_results, key=lambda k: (val_results[k]['pr_auc'], val_results[k]['roc_auc']))
    best_model = val_results[best_name]['model']
    best_val_probs = val_results[best_name]['val_probs']
    logger.info("Champion: %s (PR-AUC: %.4f)", best_name, val_results[best_name]['pr_auc'])

    # ── 6. THRESHOLD CALIBRATION ─────────────────────────────
    logger.info("Step 5: Threshold optimization...")
    candidate_thresholds = np.linspace(0.05, 0.95, 37)
    best_threshold, best_f1 = 0.5, -1.0
    best_metrics_at_thresh = {}
    threshold_analysis = []

    for th in candidate_thresholds:
        preds = (best_val_probs >= th).astype(int)
        p = precision_score(y_val, preds, zero_division=0)
        r = recall_score(y_val, preds, zero_division=0)
        f1 = f1_score(y_val, preds, zero_division=0)
        threshold_analysis.append({"threshold": round(float(th), 3),
                                   "precision": round(float(p), 4),
                                   "recall": round(float(r), 4),
                                   "f1": round(float(f1), 4)})
        if f1 > best_f1 or (abs(f1 - best_f1) < 1e-4 and r > best_metrics_at_thresh.get('recall', 0)):
            best_f1 = f1
            best_threshold = round(float(th), 3)
            best_metrics_at_thresh = {"threshold": best_threshold, "precision": float(p),
                                      "recall": float(r), "f1": float(f1)}

    logger.info("Optimal Threshold: %.3f (Val F1: %.4f)", best_threshold, best_metrics_at_thresh.get('f1', 0))

    # ── 7. TEST EVALUATION ───────────────────────────────────
    logger.info("Step 6: Test set evaluation...")
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
        "confusion_matrix": {"true_negatives": int(tn), "false_positives": int(fp),
                              "false_negatives": int(fn), "true_positives": int(tp)},
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "selected_threshold": best_threshold
    }
    logger.info("Test: PR-AUC=%.4f ROC-AUC=%.4f Recall=%.4f Prec=%.4f F1=%.4f",
                test_pr_auc, test_roc_auc, test_rec, test_prec, test_f1)

    # ── 8. SHAP ──────────────────────────────────────────────
    logger.info("Step 7: SHAP explainability...")
    top_features = []
    if isinstance(best_model, xgb.XGBClassifier):
        try:
            explainer = shap.TreeExplainer(best_model)
            sample_idx = np.random.choice(len(X_test_proc), min(1000, len(X_test_proc)), replace=False)
            shap_values = explainer.shap_values(X_test_proc[sample_idx])
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            for i in np.argsort(mean_abs_shap)[::-1][:15]:
                feat = all_feature_names[i]
                top_features.append({"feature": feat, "importance": float(mean_abs_shap[i])})
        except Exception as e:
            logger.warning("SHAP failed: %s", e)

    # ── 9. PERSIST ───────────────────────────────────────────
    logger.info("Step 8: Persisting artifacts...")
    joblib.dump(best_model, os.path.join(MODEL_DIR, "model.joblib"))
    joblib.dump(preprocessor, os.path.join(MODEL_DIR, "preprocessor.joblib"))

    feature_schema = {
        "required_raw_features": numeric_cols,
        "categorical_columns": [],
        "numeric_columns": numeric_cols,
        "all_transformed_feature_names": all_feature_names,
    }
    with open(os.path.join(MODEL_DIR, "feature_schema.json"), "w") as f:
        json.dump(feature_schema, f, indent=2)

    with open(os.path.join(MODEL_DIR, "label_mapping.json"), "w") as f:
        json.dump({"0": "LICIT", "1": "ILLICIT_FRAUD"}, f, indent=2)

    with open(os.path.join(MODEL_DIR, "threshold.json"), "w") as f:
        json.dump({"optimal_threshold": best_threshold, "default_threshold": 0.5,
                   "optimization_metric": "F1_with_Recall_priority",
                   "validation_search": threshold_analysis}, f, indent=2)

    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(test_metrics, f, indent=2)

    metadata = {
        "model_name": "bitcoin_fraud_detector",
        "domain": "CRYPTO_BITCOIN",
        "dataset_name": "elliptic_bitcoin",
        "algorithm": best_name,
        "train_rows": len(X_train),
        "val_rows": len(X_val),
        "test_rows": len(X_test),
        "fraud_ratio": float(df_labeled[TARGET_COL].mean()),
        "selected_threshold": best_threshold,
        "test_metrics": test_metrics,
        "top_features": top_features,
        "status": "READY"
    }
    with open(os.path.join(MODEL_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    with open(os.path.join(MODEL_DIR, "README.md"), "w") as f:
        f.write(f"""# Bitcoin Illicit Transaction Detector

- **Model ID**: `bitcoin_fraud_detector`
- **Algorithm**: `{best_name}`
- **Test PR-AUC**: `{test_pr_auc:.4f}`
- **Test F1**: `{test_f1:.4f}`
""")

    eval_report = f"""# Model Evaluation: Bitcoin Fraud

**Champion**: `{best_name}` | **Threshold**: `{best_threshold}`

## 1. Test Set Performance

- **PR-AUC**: `{test_pr_auc:.4f}`
- **ROC-AUC**: `{test_roc_auc:.4f}`
- **Recall**: `{test_rec:.4f}`
- **Precision**: `{test_prec:.4f}`
- **F1**: `{test_f1:.4f}`

### Confusion Matrix
| | Predicted Legit | Predicted Illicit |
| :--- | :--- | :--- |
| **Actual Legit** | {tn:,} | {fp:,} |
| **Actual Illicit** | {fn:,} | {tp:,} |
"""
    with open(os.path.join(REPORTS_DIR, "bitcoin_evaluation_report.md"), "w") as f:
        f.write(eval_report)

    logger.info("Bitcoin Pipeline Completed Successfully!")
    return metadata


if __name__ == "__main__":
    run_bitcoin_pipeline()
