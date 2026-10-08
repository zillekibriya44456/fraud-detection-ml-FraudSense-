"""
Bank Account Fraud Detection Training Pipeline
================================================
Dataset: dataset/Bank transactions/Base.csv
  - 1,000,000 rows | 31 features | Target: fraud_bool
  - Fraud rate: ~1.1% (11,029 frauds)
  - Source: BankSim / Bank Account Fraud (BAF) Benchmark Suite
  - Features: behavioral, velocity, device, credit risk, identity signals
  - No missing values, no duplicates

Pipeline:
  1. Data Quality + Leakage Audit
  2. Feature Engineering (interactions, flags, ratio features)
  3. Stratified 70/15/15 Train/Val/Test Split
  4. ColumnTransformer preprocessing (fit on train only)
  5. Train LR, RandomForest, XGBoost - compare on Val by PR-AUC
  6. Threshold calibration on Val set (maximize F1 w/ recall priority)
  7. Final test evaluation (untouched)
  8. SHAP TreeExplainer (XGBoost)
  9. Persist artifacts to models/bank/
  10. Generate reports/
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
logger = logging.getLogger("bank_pipeline")

DATA_PATH = "dataset/Bank transactions/Base.csv"
MODEL_DIR = "models/bank"
REPORTS_DIR = "reports"
TARGET_COL = "fraud_bool"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# 1. LEAKAGE & QUALITY REPORTS
# ─────────────────────────────────────────────────────────────
def generate_reports(df: pd.DataFrame):
    logger.info("Generating Data Quality and Leakage reports...")

    row_count = int(len(df))
    col_count = int(len(df.columns))
    total_missing = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    fraud_count = int((df[TARGET_COL] == 1).sum())
    legit_count = int((df[TARGET_COL] == 0).sum())
    fraud_pct = float(fraud_count / row_count * 100)

    quality_json = {
        "dataset_name": "bank_transactions_base",
        "domain": "BANK",
        "row_count": row_count,
        "column_count": col_count,
        "total_missing_values": total_missing,
        "duplicate_rows": duplicate_rows,
        "fraud_count": fraud_count,
        "legitimate_count": legit_count,
        "fraud_percentage": fraud_pct,
        "columns": {col: str(df[col].dtype) for col in df.columns}
    }
    with open(os.path.join(REPORTS_DIR, "bank_quality_report.json"), "w") as f:
        json.dump(quality_json, f, indent=2)

    quality_md = f"""# Data Quality Report: Bank Account Fraud Detection

**Dataset**: `dataset/Bank transactions/Base.csv`
**Domain**: Bank Account Fraud
**Target Column**: `fraud_bool`

## 1. Summary Statistics
- **Total Records**: {row_count:,}
- **Total Columns**: {col_count}
- **Missing Values**: {total_missing}
- **Duplicate Records**: {duplicate_rows}
- **Legitimate Transactions**: {legit_count:,} ({100 - fraud_pct:.2f}%)
- **Fraudulent Transactions**: {fraud_count:,} ({fraud_pct:.2f}%)
- **Class Imbalance Ratio**: 1 : {int(legit_count / max(1, fraud_count))}

## 2. Feature Schema
| Column Name | Data Type | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- |
"""
    for col in df.columns:
        dt = str(df[col].dtype)
        nu = int(df[col].nunique())
        sm = str(df[col].dropna().iloc[0]) if not df[col].empty else "N/A"
        quality_md += f"| `{col}` | {dt} | {nu} | {sm} |\n"

    with open(os.path.join(REPORTS_DIR, "bank_quality_report.md"), "w") as f:
        f.write(quality_md)

    leakage_md = """# Data Leakage Audit: Bank Account Fraud Detection

**Dataset**: `Base.csv`
**Target**: `fraud_bool`

## Feature Assessment

| Feature | Classification | Rationale | Action |
| :--- | :--- | :--- | :--- |
| `income` | SAFE | Normalized applicant income. Available at application time. | RETAINED |
| `name_email_similarity` | SAFE | Similarity score between name and email. Available at request time. | RETAINED |
| `prev_address_months_count` | SAFE | Months at previous address. KYC data. | RETAINED |
| `current_address_months_count` | SAFE | Months at current address. KYC data. | RETAINED |
| `customer_age` | SAFE | Applicant age. KYC data. | RETAINED |
| `days_since_request` | SAFE | Days since initial request. Available at time of scoring. | RETAINED |
| `intended_balcon_amount` | SAFE | Intended balance/amount transferred in. Available at time of request. | RETAINED |
| `payment_type` | SAFE | Payment channel type. Available at request. | RETAINED |
| `zip_count_4w` | SAFE | Zip code request frequency in 4 weeks. Velocity feature, available at scoring. | RETAINED |
| `velocity_6h` | SAFE | Number of requests in 6h window. Pre-decision velocity signal. | RETAINED |
| `velocity_24h` | SAFE | Number of requests in 24h window. Pre-decision velocity signal. | RETAINED |
| `velocity_4w` | SAFE | Number of requests in 4w window. Pre-decision velocity signal. | RETAINED |
| `bank_branch_count_8w` | SAFE | Unique bank branch visits in 8 weeks. Available at scoring. | RETAINED |
| `date_of_birth_distinct_emails_4w` | SAFE | Distinct emails with same DOB in 4w. Identity signal. | RETAINED |
| `employment_status` | SAFE | Employment category. KYC data. | RETAINED |
| `credit_risk_score` | SAFE | Bureau credit risk score. Available at decision time. | RETAINED |
| `email_is_free` | SAFE | Free email provider flag. Available at request. | RETAINED |
| `housing_status` | SAFE | Applicant housing type. KYC data. | RETAINED |
| `phone_home_valid` | SAFE | Home phone validation flag. Available at scoring. | RETAINED |
| `phone_mobile_valid` | SAFE | Mobile phone validation flag. Available at scoring. | RETAINED |
| `bank_months_count` | SAFE | Months with current bank. KYC/CRM data. | RETAINED |
| `has_other_cards` | SAFE | Whether applicant holds other cards. Bureau data. | RETAINED |
| `proposed_credit_limit` | SAFE | Proposed credit limit at application. Available at request. | RETAINED |
| `foreign_request` | SAFE | Whether request originated from foreign IP. | RETAINED |
| `source` | SAFE | Request source (INTERNET, TELEAPP, etc.). | RETAINED |
| `session_length_in_minutes` | SAFE | Session duration. Available at decision time. | RETAINED |
| `device_os` | SAFE | Device operating system. Client signal. | RETAINED |
| `keep_alive_session` | SAFE | Session keep-alive flag. Client behavioral signal. | RETAINED |
| `device_distinct_emails_8w` | SAFE | Distinct emails from device in 8 weeks. Device fingerprint signal. | RETAINED |
| `device_fraud_count` | **POTENTIAL_LEAKAGE** | Historical fraud count on device. If computed on post-decision data, it could leak. Treated as safe if computed on prior transactions only. | RETAINED (with caution) |
| `month` | SAFE | Month of request (seasonality). | RETAINED |

## Leakage Prevention Protocol
- No post-decision or outcome-dependent features identified.
- `device_fraud_count` is the only borderline feature; treated as pre-computed historical signal.
- Stratified 70/15/15 split applied before preprocessing.
- Preprocessor fitted strictly on training data.
"""
    with open(os.path.join(REPORTS_DIR, "bank_leakage_report.md"), "w") as f:
        f.write(leakage_md)

    logger.info("Reports generated successfully.")


# ─────────────────────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Velocity ratio features (cross-window signals)
    df['velocity_ratio_6h_24h'] = df['velocity_6h'] / (df['velocity_24h'] + 1e-6)
    df['velocity_ratio_24h_4w'] = df['velocity_24h'] / (df['velocity_4w'] + 1e-6)

    # Identity anomaly signals
    df['identity_anomaly_score'] = (
        (1 - df['name_email_similarity']) +
        df['email_is_free'] +
        (1 - df['phone_home_valid']) +
        (1 - df['phone_mobile_valid'])
    )

    # Credit risk bucket
    df['credit_risk_bucket'] = pd.cut(
        df['credit_risk_score'],
        bins=[-np.inf, 0, 50, 100, 200, np.inf],
        labels=['negative', 'very_poor', 'poor', 'fair', 'good']
    ).astype(str)

    # New address flag (highly recent address changes = risk signal)
    df['is_new_address'] = (df['current_address_months_count'] < 6).astype(int)
    df['has_unknown_prev_address'] = (df['prev_address_months_count'] == -1).astype(int)

    # High velocity flag (top 5% velocity in 6h)
    v6h_95 = df['velocity_6h'].quantile(0.95)
    df['is_high_velocity'] = (df['velocity_6h'] > v6h_95).astype(int)

    # Device reuse risk (multiple emails on same device)
    df['device_reuse_risk'] = (df['device_distinct_emails_8w'] > 1).astype(int)

    # Log transform skewed features
    for col in ['velocity_6h', 'velocity_24h', 'velocity_4w', 'zip_count_4w', 'session_length_in_minutes']:
        df[f'log_{col}'] = np.log1p(df[col].clip(lower=0))

    return df


# ─────────────────────────────────────────────────────────────
# 3. MAIN PIPELINE
# ─────────────────────────────────────────────────────────────
def run_bank_pipeline():
    logger.info("Step 1: Loading Bank Transactions dataset...")
    raw_df = pd.read_csv(DATA_PATH)
    logger.info("Loaded %d rows x %d columns.", len(raw_df), len(raw_df.columns))

    generate_reports(raw_df)

    logger.info("Step 2: Feature Engineering...")
    df = engineer_features(raw_df)

    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

    # ── 3. STRATIFIED SPLIT ──────────────────────────────────
    logger.info("Step 3: Stratified 70/15/15 Train/Val/Test Split...")
    X_tv, X_test, y_tv, y_test = train_test_split(
        X, y, test_size=0.15, stratify=y, random_state=42
    )
    val_ratio = 0.15 / 0.85
    X_train, X_val, y_train, y_val = train_test_split(
        X_tv, y_tv, test_size=val_ratio, stratify=y_tv, random_state=42
    )
    logger.info("Train: %d (fraud: %d) | Val: %d (fraud: %d) | Test: %d (fraud: %d)",
                len(X_train), int(y_train.sum()),
                len(X_val), int(y_val.sum()),
                len(X_test), int(y_test.sum()))

    # ── 4. PREPROCESSING ────────────────────────────────────
    categorical_cols = [
        'payment_type', 'employment_status', 'housing_status',
        'source', 'device_os', 'credit_risk_bucket'
    ]
    numeric_cols = [col for col in X_train.columns if col not in categorical_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
        ]
    )

    logger.info("Step 4: Fitting preprocessor on Train set only...")
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)

    cat_feature_names = list(preprocessor.named_transformers_['cat'].get_feature_names_out(categorical_cols))
    all_feature_names = numeric_cols + cat_feature_names

    scale_pos_weight = float((y_train == 0).sum() / max(1, (y_train == 1).sum()))
    logger.info("scale_pos_weight: %.2f (fraud rate: %.3f%%)", scale_pos_weight, y_train.mean() * 100)

    # ── 5. MODEL TRAINING ───────────────────────────────────
    models = {
        "LogisticRegression": LogisticRegression(
            class_weight='balanced', max_iter=1000, C=0.5, random_state=42
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_leaf=2,
            class_weight='balanced', random_state=42, n_jobs=-1
        ),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=400,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            scale_pos_weight=scale_pos_weight,
            eval_metric='aucpr',
            tree_method='hist',
            random_state=42,
            n_jobs=-1
        ),
    }

    logger.info("Step 5: Training and comparing candidate models...")
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
            "model": model,
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "f1_default": f1,
            "recall_default": rec,
            "precision_default": prec,
            "val_probs": val_probs
        }
        logger.info("[%s] Val PR-AUC: %.4f | ROC-AUC: %.4f | F1@0.5: %.4f | Recall@0.5: %.4f",
                    name, pr_auc, roc_auc, f1, rec)

    best_model_name = max(val_results, key=lambda k: (val_results[k]['pr_auc'], val_results[k]['roc_auc']))
    best_model = val_results[best_model_name]['model']
    best_val_probs = val_results[best_model_name]['val_probs']
    logger.info("Champion: %s (PR-AUC: %.4f)", best_model_name, val_results[best_model_name]['pr_auc'])

    # ── 6. THRESHOLD CALIBRATION ────────────────────────────
    logger.info("Step 6: Optimizing decision threshold on Validation Set...")
    candidate_thresholds = np.linspace(0.05, 0.95, 37)
    best_threshold = 0.5
    best_f1 = -1.0
    best_metrics_at_thresh = {}
    threshold_analysis = []

    for th in candidate_thresholds:
        preds = (best_val_probs >= th).astype(int)
        p = precision_score(y_val, preds, zero_division=0)
        r = recall_score(y_val, preds, zero_division=0)
        f1 = f1_score(y_val, preds, zero_division=0)
        threshold_analysis.append({
            "threshold": round(float(th), 3),
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(f1), 4)
        })
        if f1 > best_f1 or (abs(f1 - best_f1) < 1e-4 and r > best_metrics_at_thresh.get('recall', 0)):
            best_f1 = f1
            best_threshold = round(float(th), 3)
            best_metrics_at_thresh = {"threshold": best_threshold, "precision": float(p),
                                      "recall": float(r), "f1": float(f1)}

    logger.info("Optimal Threshold: %.3f (Val F1: %.4f, Prec: %.4f, Recall: %.4f)",
                best_threshold, best_metrics_at_thresh.get('f1', 0),
                best_metrics_at_thresh.get('precision', 0),
                best_metrics_at_thresh.get('recall', 0))

    # ── 7. TEST EVALUATION ──────────────────────────────────
    logger.info("Step 7: Evaluating on Untouched Test Set...")
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
    logger.info("Test: PR-AUC=%.4f ROC-AUC=%.4f Recall=%.4f Prec=%.4f F1=%.4f TP=%d FP=%d FN=%d",
                test_pr_auc, test_roc_auc, test_rec, test_prec, test_f1, tp, fp, fn)

    # ── 8. SHAP EXPLAINABILITY ──────────────────────────────
    logger.info("Step 8: Computing SHAP values...")
    top_features = []
    if isinstance(best_model, xgb.XGBClassifier):
        try:
            explainer = shap.TreeExplainer(best_model)
            sample_idx = np.random.choice(len(X_test_proc), min(1000, len(X_test_proc)), replace=False)
            shap_values = explainer.shap_values(X_test_proc[sample_idx])
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            sorted_idx = np.argsort(mean_abs_shap)[::-1]
            for i in sorted_idx[:15]:
                feat = all_feature_names[i] if i < len(all_feature_names) else f"feature_{i}"
                top_features.append({"feature": feat, "importance": float(mean_abs_shap[i])})
        except Exception as e:
            logger.warning("SHAP failed: %s", e)

    # ── 9. PERSIST ARTIFACTS ────────────────────────────────
    logger.info("Step 9: Saving artifacts to %s...", MODEL_DIR)
    joblib.dump(best_model, os.path.join(MODEL_DIR, "model.joblib"))
    joblib.dump(preprocessor, os.path.join(MODEL_DIR, "preprocessor.joblib"))

    feature_schema = {
        "required_raw_features": list(raw_df.drop(columns=[TARGET_COL]).columns),
        "engineered_features": [
            "velocity_ratio_6h_24h", "velocity_ratio_24h_4w",
            "identity_anomaly_score", "credit_risk_bucket",
            "is_new_address", "has_unknown_prev_address",
            "is_high_velocity", "device_reuse_risk",
            "log_velocity_6h", "log_velocity_24h", "log_velocity_4w",
            "log_zip_count_4w", "log_session_length_in_minutes"
        ],
        "categorical_columns": categorical_cols,
        "numeric_columns": numeric_cols,
        "all_transformed_feature_names": all_feature_names
    }
    with open(os.path.join(MODEL_DIR, "feature_schema.json"), "w") as f:
        json.dump(feature_schema, f, indent=2)

    with open(os.path.join(MODEL_DIR, "label_mapping.json"), "w") as f:
        json.dump({"0": "LEGITIMATE", "1": "FRAUD"}, f, indent=2)

    with open(os.path.join(MODEL_DIR, "threshold.json"), "w") as f:
        json.dump({
            "optimal_threshold": best_threshold,
            "default_threshold": 0.50,
            "optimization_metric": "F1_with_Recall_priority",
            "validation_search": threshold_analysis
        }, f, indent=2)

    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(test_metrics, f, indent=2)

    metadata = {
        "model_name": "bank_fraud_detector",
        "domain": "BANK",
        "dataset_name": "bank_transactions_base",
        "dataset_file": "dataset/Bank transactions/Base.csv",
        "algorithm": best_model_name,
        "train_rows": len(X_train),
        "val_rows": len(X_val),
        "test_rows": len(X_test),
        "fraud_ratio": float(y.mean()),
        "scale_pos_weight": scale_pos_weight,
        "selected_threshold": best_threshold,
        "test_metrics": test_metrics,
        "top_features": top_features,
        "leakage_exclusions": [],
        "status": "READY"
    }
    with open(os.path.join(MODEL_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    readme = f"""# Bank Account Fraud Detection Model

- **Model ID**: `bank_fraud_detector`
- **Domain**: `BANK`
- **Algorithm**: `{best_model_name}`
- **Test PR-AUC**: `{test_pr_auc:.4f}`
- **Test ROC-AUC**: `{test_roc_auc:.4f}`
- **Test Recall**: `{test_rec:.4f}` ({tp} of {tp + fn} frauds detected)
- **Test Precision**: `{test_prec:.4f}`
- **Test F1**: `{test_f1:.4f}`
- **Optimal Threshold**: `{best_threshold}`

## Artifacts
- `model.joblib`, `preprocessor.joblib`
- `feature_schema.json`, `threshold.json`, `metrics.json`, `metadata.json`
"""
    with open(os.path.join(MODEL_DIR, "README.md"), "w") as f:
        f.write(readme)

    # ── 10. EVALUATION REPORT ───────────────────────────────
    eval_report = f"""# Model Evaluation Report: Bank Account Fraud Detection

**Dataset**: `dataset/Bank transactions/Base.csv`
**Champion**: `{best_model_name}` | **Threshold**: `{best_threshold}`

## 1. Candidate Model Comparison (Validation Set)

| Model | PR-AUC | ROC-AUC | F1@0.5 | Recall@0.5 | Precision@0.5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression** | {val_results['LogisticRegression']['pr_auc']:.4f} | {val_results['LogisticRegression']['roc_auc']:.4f} | {val_results['LogisticRegression']['f1_default']:.4f} | {val_results['LogisticRegression']['recall_default']:.4f} | {val_results['LogisticRegression']['precision_default']:.4f} |
| **Random Forest** | {val_results['RandomForest']['pr_auc']:.4f} | {val_results['RandomForest']['roc_auc']:.4f} | {val_results['RandomForest']['f1_default']:.4f} | {val_results['RandomForest']['recall_default']:.4f} | {val_results['RandomForest']['precision_default']:.4f} |
| **XGBoost** | **{val_results['XGBoost']['pr_auc']:.4f}** | **{val_results['XGBoost']['roc_auc']:.4f}** | **{val_results['XGBoost']['f1_default']:.4f}** | **{val_results['XGBoost']['recall_default']:.4f}** | **{val_results['XGBoost']['precision_default']:.4f}** |

## 2. Threshold Calibration (Validation Set)

| Threshold | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- |
"""
    for row in threshold_analysis:
        marker = " **(Selected)**" if row['threshold'] == best_threshold else ""
        eval_report += f"| `{row['threshold']}` | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f}{marker} |\n"

    eval_report += f"""
## 3. Untouched Test Set Performance

- **Accuracy**: `{test_acc * 100:.2f}%`
- **Precision**: `{test_prec:.4f}`
- **Recall**: `{test_rec:.4f}`
- **F1-Score**: `{test_f1:.4f}`
- **PR-AUC**: `{test_pr_auc:.4f}`
- **ROC-AUC**: `{test_roc_auc:.4f}`
- **FPR**: `{fpr:.4f}` ({fp:,} false alarms)
- **FNR**: `{fnr:.4f}` ({fn:,} missed frauds)

### Confusion Matrix
| | Predicted Legitimate | Predicted Fraud |
| :--- | :--- | :--- |
| **Actual Legitimate** | {tn:,} (TN) | {fp:,} (FP) |
| **Actual Fraud** | {fn:,} (FN) | {tp:,} (TP) |

## 4. Top SHAP Features
| Rank | Feature | Mean |SHAP| |
| :--- | :--- | :--- |
"""
    for i, tf in enumerate(top_features[:10], 1):
        eval_report += f"| {i} | `{tf['feature']}` | {tf['importance']:.4f} |\n"

    with open(os.path.join(REPORTS_DIR, "bank_evaluation_report.md"), "w") as f:
        f.write(eval_report)

    logger.info("Bank Training Pipeline Completed Successfully!")
    return metadata


if __name__ == "__main__":
    run_bank_pipeline()
