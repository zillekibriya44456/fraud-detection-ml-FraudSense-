"""
PaySim Mobile Money Fraud Detection Training Pipeline
=======================================================
Dataset: dataset/PS_20174392719_1491204439457_log.csv
  - 6,362,620 rows | 10 features | Target: isFraud
  - Fraud rate: 0.129% (8,213 frauds)
  - Key insight: Fraud ONLY occurs in TRANSFER and CASH_OUT transactions
  - Features: step, type, amount, balance changes (origin & dest)
  - isFlaggedFraud: internal bank rule (only flags 16 cases) — DROPPED to avoid leakage

Pipeline:
  1. Data Quality + Leakage Audit
  2. Feature Engineering (balance error flags, zero-balance traps, log features)
  3. Filter to TRANSFER+CASH_OUT only (where fraud occurs) for efficient training
  4. Stratified 70/15/15 Train/Val/Test Split
  5. Preprocessing (fit on train only)
  6. Train LR, RandomForest, XGBoost - compare on Val PR-AUC
  7. Threshold calibration on Val
  8. Final test evaluation
  9. SHAP explainability
  10. Persist artifacts to models/paysim/
"""
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
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)
import shap

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("paysim_pipeline")

DATA_PATH = "dataset/PS_20174392719_1491204439457_log.csv"
MODEL_DIR = "models/paysim"
REPORTS_DIR = "reports"
TARGET_COL = "isFraud"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# 1. REPORTS
# ─────────────────────────────────────────────────────────────
def generate_reports(df: pd.DataFrame):
    logger.info("Generating Data Quality and Leakage reports...")

    row_count = int(len(df))
    col_count = int(len(df.columns))
    fraud_count = int((df[TARGET_COL] == 1).sum())
    legit_count = int((df[TARGET_COL] == 0).sum())
    fraud_pct = float(fraud_count / row_count * 100)
    fraud_types = df[df[TARGET_COL] == 1]['type'].value_counts().to_dict()

    quality_json = {
        "dataset_name": "paysim_mobile_money",
        "domain": "MOBILE_MONEY",
        "row_count": row_count,
        "column_count": col_count,
        "total_missing_values": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "fraud_count": fraud_count,
        "legitimate_count": legit_count,
        "fraud_percentage": fraud_pct,
        "fraud_by_type": {k: int(v) for k, v in fraud_types.items()},
        "key_insight": "Fraud ONLY occurs in TRANSFER and CASH_OUT transactions.",
        "columns": {col: str(df[col].dtype) for col in df.columns}
    }
    with open(os.path.join(REPORTS_DIR, "paysim_quality_report.json"), "w") as f:
        json.dump(quality_json, f, indent=2)

    quality_md = f"""# Data Quality Report: PaySim Mobile Money

**Dataset**: `dataset/PS_20174392719_1491204439457_log.csv`
**Domain**: Mobile Money / PaySim
**Target Column**: `isFraud`

## 1. Summary Statistics
- **Total Records**: {row_count:,}
- **Total Columns**: {col_count}
- **Missing Values**: 0
- **Fraudulent Transactions**: {fraud_count:,} ({fraud_pct:.3f}%)
- **Legitimate Transactions**: {legit_count:,} ({100 - fraud_pct:.3f}%)
- **Class Imbalance**: 1 : {int(legit_count / max(1, fraud_count))}

## 2. Key Insight
> Fraud occurs **exclusively** in `TRANSFER` and `CASH_OUT` transactions.
> PAYMENT, CASH_IN, and DEBIT transactions have **zero** fraud cases.
> Training is performed on the filtered TRANSFER+CASH_OUT subset.

| Fraud by Type | Count |
|---|---|
| CASH_OUT | {fraud_types.get('CASH_OUT', 0):,} |
| TRANSFER | {fraud_types.get('TRANSFER', 0):,} |
"""
    with open(os.path.join(REPORTS_DIR, "paysim_quality_report.md"), "w") as f:
        f.write(quality_md)

    leakage_md = """# Data Leakage Audit: PaySim Mobile Money

**Dataset**: `PS_20174392719_1491204439457_log.csv`
**Target**: `isFraud`

## Feature Assessment

| Feature | Classification | Rationale | Action |
| :--- | :--- | :--- | :--- |
| `step` | SAFE | Simulated time step (1 step = 1 hour). Temporal signal. | RETAINED |
| `type` | SAFE | Transaction type (TRANSFER/CASH_OUT). Available at authorization. | RETAINED |
| `amount` | SAFE | Transaction amount. Available at authorization. | RETAINED |
| `nameOrig` | DEFINITE_LEAKAGE | Customer ID — unique entity identifier. Induces memorization. | **DROPPED** |
| `oldbalanceOrg` | SAFE | Originator balance before transaction. Available at authorization. | RETAINED |
| `newbalanceOrig` | **POTENTIAL_LEAKAGE** | Originator balance AFTER transaction. Post-event signal. Used carefully — retained as it reveals zero-drain patterns. | RETAINED with caution |
| `nameDest` | DEFINITE_LEAKAGE | Destination ID — unique entity. | **DROPPED** |
| `oldbalanceDest` | SAFE | Destination balance before transaction. Available at authorization. | RETAINED |
| `newbalanceDest` | **POTENTIAL_LEAKAGE** | Destination balance AFTER. Post-event; retained for zero-balance trap detection. | RETAINED with caution |
| `isFlaggedFraud` | **DEFINITE_LEAKAGE** | Bank's own fraud flag — computed post-decision. Only 16 flags in 6.3M rows (useless and leaky). | **DROPPED** |

## Leakage Prevention Protocol
- `nameOrig`, `nameDest`, `isFlaggedFraud` dropped before training.
- `newbalanceOrig` and `newbalanceDest` retained because they encode the key fraud pattern
  (complete drain of origin account + zero dest balance = strong signal).
- Stratified 70/15/15 split on TRANSFER+CASH_OUT filtered subset.
- Preprocessor fitted strictly on training data.
"""
    with open(os.path.join(REPORTS_DIR, "paysim_leakage_report.md"), "w") as f:
        f.write(leakage_md)

    logger.info("Reports generated.")


# ─────────────────────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Feature 1: Balance error — difference between what SHOULD happen and what DID
    # For a legitimate transaction: newbalanceOrig = oldbalanceOrg - amount
    df['balance_error_orig'] = df['newbalanceOrig'] - (df['oldbalanceOrg'] - df['amount'])

    # Feature 2: Same pattern for destination
    df['balance_error_dest'] = df['newbalanceDest'] - (df['oldbalanceDest'] + df['amount'])

    # Feature 3: Zero-drain flag — origin drained to zero
    df['orig_drained_to_zero'] = ((df['oldbalanceOrg'] > 0) & (df['newbalanceOrig'] == 0)).astype(int)

    # Feature 4: Destination account never received funds
    df['dest_no_change'] = ((df['oldbalanceDest'] == df['newbalanceDest']) & (df['amount'] > 0)).astype(int)

    # Feature 5: Amount relative to original balance
    df['amount_ratio_orig'] = df['amount'] / (df['oldbalanceOrg'] + 1.0)

    # Feature 6: Log transforms
    df['log_amount'] = np.log1p(df['amount'])
    df['log_oldbalanceOrg'] = np.log1p(df['oldbalanceOrg'])
    df['log_oldbalanceDest'] = np.log1p(df['oldbalanceDest'])

    # Feature 7: Transaction at unusual time (late night in simulation)
    df['is_unusual_hour'] = ((df['step'] % 24) < 6).astype(int)

    # Drop leakage columns
    df = df.drop(columns=['nameOrig', 'nameDest', 'isFlaggedFraud'])

    return df


# ─────────────────────────────────────────────────────────────
# 3. MAIN PIPELINE
# ─────────────────────────────────────────────────────────────
def run_paysim_pipeline():
    logger.info("Step 1: Loading PaySim dataset...")
    raw_df = pd.read_csv(DATA_PATH)
    logger.info("Loaded %d rows x %d columns.", len(raw_df), len(raw_df.columns))

    generate_reports(raw_df)

    # KEY: Filter to only TRANSFER + CASH_OUT (only types with fraud)
    logger.info("Filtering to TRANSFER + CASH_OUT transactions (only fraud-relevant types)...")
    filtered_df = raw_df[raw_df['type'].isin(['TRANSFER', 'CASH_OUT'])].copy()
    logger.info("Filtered size: %d rows | Fraud: %d (%.3f%%)",
                len(filtered_df), filtered_df[TARGET_COL].sum(),
                filtered_df[TARGET_COL].mean() * 100)

    logger.info("Step 2: Feature Engineering...")
    df = engineer_features(filtered_df)

    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

    # ── 3. SPLIT ────────────────────────────────────────────
    logger.info("Step 3: Stratified 70/15/15 split...")
    X_tv, X_test, y_tv, y_test = train_test_split(
        X, y, test_size=0.15, stratify=y, random_state=42
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_tv, y_tv, test_size=0.15 / 0.85, stratify=y_tv, random_state=42
    )
    logger.info("Train: %d (fraud: %d) | Val: %d (fraud: %d) | Test: %d (fraud: %d)",
                len(X_train), int(y_train.sum()),
                len(X_val), int(y_val.sum()),
                len(X_test), int(y_test.sum()))

    # ── 4. PREPROCESSING ─────────────────────────────────────
    categorical_cols = ['type']
    numeric_cols = [c for c in X_train.columns if c not in categorical_cols]

    preprocessor = ColumnTransformer([
        ('num', StandardScaler(), numeric_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
    ])

    logger.info("Step 4: Fitting preprocessor on Train set only...")
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)

    cat_names = list(preprocessor.named_transformers_['cat'].get_feature_names_out(categorical_cols))
    all_feature_names = numeric_cols + cat_names

    scale_pos_weight = float((y_train == 0).sum() / max(1, (y_train == 1).sum()))
    logger.info("scale_pos_weight: %.2f (fraud rate: %.3f%%)", scale_pos_weight, y_train.mean() * 100)

    # ── 5. TRAIN MODELS ──────────────────────────────────────
    models = {
        "LogisticRegression": LogisticRegression(
            class_weight='balanced', max_iter=1000, C=1.0, random_state=42
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_leaf=2,
            class_weight='balanced', random_state=42, n_jobs=-1
        ),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            scale_pos_weight=scale_pos_weight,
            eval_metric='aucpr',
            tree_method='hist',
            random_state=42,
            n_jobs=-1
        ),
    }

    logger.info("Step 5: Training candidate models...")
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
        logger.info("[%s] Val PR-AUC: %.4f | ROC-AUC: %.4f | F1@0.5: %.4f | Recall@0.5: %.4f",
                    name, pr_auc, roc_auc, f1, rec)

    best_name = max(val_results, key=lambda k: (val_results[k]['pr_auc'], val_results[k]['roc_auc']))
    best_model = val_results[best_name]['model']
    best_val_probs = val_results[best_name]['val_probs']
    logger.info("Champion: %s (PR-AUC: %.4f)", best_name, val_results[best_name]['pr_auc'])

    # ── 6. THRESHOLD CALIBRATION ─────────────────────────────
    logger.info("Step 6: Threshold optimization...")
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

    logger.info("Optimal Threshold: %.3f (Val F1: %.4f, Prec: %.4f, Recall: %.4f)",
                best_threshold, best_metrics_at_thresh.get('f1', 0),
                best_metrics_at_thresh.get('precision', 0),
                best_metrics_at_thresh.get('recall', 0))

    # ── 7. TEST EVALUATION ───────────────────────────────────
    logger.info("Step 7: Test set evaluation...")
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
    logger.info("Test: PR-AUC=%.4f ROC-AUC=%.4f Recall=%.4f Prec=%.4f F1=%.4f TP=%d FP=%d FN=%d",
                test_pr_auc, test_roc_auc, test_rec, test_prec, test_f1, tp, fp, fn)

    # ── 8. SHAP ──────────────────────────────────────────────
    logger.info("Step 8: SHAP explainability...")
    top_features = []
    if isinstance(best_model, xgb.XGBClassifier):
        try:
            explainer = shap.TreeExplainer(best_model)
            sample_idx = np.random.choice(len(X_test_proc), min(1000, len(X_test_proc)), replace=False)
            shap_values = explainer.shap_values(X_test_proc[sample_idx])
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            for i in np.argsort(mean_abs_shap)[::-1][:15]:
                feat = all_feature_names[i] if i < len(all_feature_names) else f"feat_{i}"
                top_features.append({"feature": feat, "importance": float(mean_abs_shap[i])})
        except Exception as e:
            logger.warning("SHAP failed: %s", e)

    # ── 9. PERSIST ───────────────────────────────────────────
    logger.info("Step 9: Persisting artifacts...")
    joblib.dump(best_model, os.path.join(MODEL_DIR, "model.joblib"))
    joblib.dump(preprocessor, os.path.join(MODEL_DIR, "preprocessor.joblib"))

    feature_schema = {
        "required_raw_features": ["step", "type", "amount",
                                   "oldbalanceOrg", "newbalanceOrig",
                                   "oldbalanceDest", "newbalanceDest"],
        "engineered_features": [
            "balance_error_orig", "balance_error_dest",
            "orig_drained_to_zero", "dest_no_change",
            "amount_ratio_orig", "log_amount",
            "log_oldbalanceOrg", "log_oldbalanceDest", "is_unusual_hour"
        ],
        "categorical_columns": categorical_cols,
        "numeric_columns": numeric_cols,
        "all_transformed_feature_names": all_feature_names,
        "eligible_types": ["TRANSFER", "CASH_OUT"],
        "note": "Model trained on TRANSFER+CASH_OUT only. Other types assumed LEGITIMATE."
    }
    with open(os.path.join(MODEL_DIR, "feature_schema.json"), "w") as f:
        json.dump(feature_schema, f, indent=2)

    with open(os.path.join(MODEL_DIR, "label_mapping.json"), "w") as f:
        json.dump({"0": "LEGITIMATE", "1": "FRAUD"}, f, indent=2)

    with open(os.path.join(MODEL_DIR, "threshold.json"), "w") as f:
        json.dump({"optimal_threshold": best_threshold, "default_threshold": 0.5,
                   "optimization_metric": "F1_with_Recall_priority",
                   "validation_search": threshold_analysis}, f, indent=2)

    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(test_metrics, f, indent=2)

    metadata = {
        "model_name": "paysim_fraud_detector",
        "domain": "MOBILE_MONEY_PAYSIM",
        "dataset_name": "paysim_mobile_money",
        "dataset_file": DATA_PATH,
        "algorithm": best_name,
        "train_rows": len(X_train),
        "val_rows": len(X_val),
        "test_rows": len(X_test),
        "total_rows_before_filter": len(raw_df),
        "filtered_to": "TRANSFER + CASH_OUT only",
        "fraud_ratio_filtered": float(y.mean()),
        "scale_pos_weight": scale_pos_weight,
        "selected_threshold": best_threshold,
        "test_metrics": test_metrics,
        "top_features": top_features,
        "leakage_exclusions": ["nameOrig", "nameDest", "isFlaggedFraud"],
        "status": "READY"
    }
    with open(os.path.join(MODEL_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    with open(os.path.join(MODEL_DIR, "README.md"), "w") as f:
        f.write(f"""# PaySim Mobile Money Fraud Detector

- **Model ID**: `paysim_fraud_detector`
- **Algorithm**: `{best_name}`
- **Trained on**: TRANSFER + CASH_OUT transactions only
- **Test PR-AUC**: `{test_pr_auc:.4f}`
- **Test ROC-AUC**: `{test_roc_auc:.4f}`
- **Test Recall**: `{test_rec:.4f}` ({tp} of {tp + fn} frauds)
- **Test Precision**: `{test_prec:.4f}`
- **Test F1**: `{test_f1:.4f}`
- **Threshold**: `{best_threshold}`
""")

    eval_report = f"""# Model Evaluation: PaySim Mobile Money Fraud

**Champion**: `{best_name}` | **Threshold**: `{best_threshold}`

## 1. Candidate Model Comparison (Validation Set)

| Model | PR-AUC | ROC-AUC | F1@0.5 | Recall@0.5 | Precision@0.5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression** | {val_results['LogisticRegression']['pr_auc']:.4f} | {val_results['LogisticRegression']['roc_auc']:.4f} | {val_results['LogisticRegression']['f1_default']:.4f} | {val_results['LogisticRegression']['recall_default']:.4f} | {val_results['LogisticRegression']['precision_default']:.4f} |
| **Random Forest** | {val_results['RandomForest']['pr_auc']:.4f} | {val_results['RandomForest']['roc_auc']:.4f} | {val_results['RandomForest']['f1_default']:.4f} | {val_results['RandomForest']['recall_default']:.4f} | {val_results['RandomForest']['precision_default']:.4f} |
| **XGBoost** | **{val_results['XGBoost']['pr_auc']:.4f}** | **{val_results['XGBoost']['roc_auc']:.4f}** | **{val_results['XGBoost']['f1_default']:.4f}** | **{val_results['XGBoost']['recall_default']:.4f}** | **{val_results['XGBoost']['precision_default']:.4f}** |

## 2. Test Set Performance

- **PR-AUC**: `{test_pr_auc:.4f}`
- **ROC-AUC**: `{test_roc_auc:.4f}`
- **Recall**: `{test_rec:.4f}`
- **Precision**: `{test_prec:.4f}`
- **F1**: `{test_f1:.4f}`
- **FPR**: `{fpr:.4f}` ({fp:,} false alarms)
- **FNR**: `{fnr:.4f}` ({fn} missed frauds)

### Confusion Matrix
| | Predicted Legit | Predicted Fraud |
| :--- | :--- | :--- |
| **Actual Legit** | {tn:,} | {fp:,} |
| **Actual Fraud** | {fn:,} | {tp:,} |

## 3. Top SHAP Features
| Rank | Feature | Mean |SHAP| |
| :--- | :--- | :--- |
"""
    for i, tf in enumerate(top_features[:10], 1):
        eval_report += f"| {i} | `{tf['feature']}` | {tf['importance']:.4f} |\n"

    with open(os.path.join(REPORTS_DIR, "paysim_evaluation_report.md"), "w") as f:
        f.write(eval_report)

    logger.info("PaySim Pipeline Completed Successfully!")
    return metadata


if __name__ == "__main__":
    run_paysim_pipeline()
