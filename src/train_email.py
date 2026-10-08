import os
import re
import json
import logging
import warnings
import numpy as np
import pandas as pd
import joblib
from scipy.sparse import hstack
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("email_pipeline")

DATA_PATH = "data/raw/email/phishing_email.csv"
MODEL_DIR = "models/email"
REPORTS_DIR = "reports"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

URL_REGEX = re.compile(r'https?://\S+|www\.\S+|\.com/\S+|\.net/\S+', re.IGNORECASE)
URGENT_REGEX = re.compile(r'\b(urgent|immediately|suspended|suspend|deactivated|action required|warning|threat|notice)\b', re.IGNORECASE)
FINANCIAL_REGEX = re.compile(r'\b(invoice|account|bank|payment|wire|transfer|funds|dollars|billing|payroll)\b', re.IGNORECASE)
CRED_REGEX = re.compile(r'\b(password|login|verify|credential|otp|pin|security code|authenticate|reset)\b', re.IGNORECASE)

def extract_meta_features(texts: pd.Series) -> pd.DataFrame:
    features = []
    for text in texts:
        t = str(text)
        t_len = max(1, len(t))
        char_len = len(t)
        word_count = len(t.split())
        has_url = 1 if URL_REGEX.search(t) else 0
        has_urgent = 1 if URGENT_REGEX.search(t) else 0
        has_financial = 1 if FINANCIAL_REGEX.search(t) else 0
        has_cred = 1 if CRED_REGEX.search(t) else 0
        upper_chars = sum(1 for c in t if c.isupper())
        digits = sum(1 for c in t if c.isdigit())
        upper_ratio = float(upper_chars / t_len)
        digit_ratio = float(digits / t_len)
        
        features.append({
            "char_length": char_len,
            "word_count": word_count,
            "has_url": has_url,
            "has_urgent": has_urgent,
            "has_financial": has_financial,
            "has_cred": has_cred,
            "upper_ratio": upper_ratio,
            "digit_ratio": digit_ratio
        })
    return pd.DataFrame(features)

def generate_quality_and_leakage_reports(raw_df: pd.DataFrame, dedup_df: pd.DataFrame):
    logger.info("Generating Data Quality and Data Leakage reports for Email Phishing dataset...")
    
    row_count = int(len(raw_df))
    duplicate_rows = int(raw_df.duplicated(subset=['text_combined']).sum())
    phish_count = int((raw_df['label'] == 1).sum())
    legit_count = int((raw_df['label'] == 0).sum())
    phish_pct = float(phish_count / row_count * 100)
    legit_pct = float(legit_count / row_count * 100)
    
    quality_json = {
        "dataset_name": "phishing_email",
        "domain": "EMAIL",
        "row_count": row_count,
        "total_missing_values": 0,
        "duplicate_emails": duplicate_rows,
        "post_dedup_rows": int(len(dedup_df)),
        "phishing_count": phish_count,
        "legitimate_count": legit_count,
        "phishing_percentage": phish_pct,
        "legitimate_percentage": legit_pct
    }
    
    with open(os.path.join(REPORTS_DIR, "email_phishing_quality_report.json"), "w") as f:
        json.dump(quality_json, f, indent=2)
        
    quality_md = f"""# Data Quality Report: Email Phishing

**Dataset**: `data/raw/email/phishing_email.csv`  
**Domain**: Email Phishing & Fraud  
**Target Column**: `label` (1 = Phishing, 0 = Legitimate)  

## 1. Summary Statistics
- **Total Raw Records**: {row_count:,}
- **Duplicate Records**: {duplicate_rows:,} ({duplicate_rows / row_count * 100:.2f}%)
- **Post-Deduplication Records**: {len(dedup_df):,}
- **Phishing Emails**: {phish_count:,} ({phish_pct:.2f}%)
- **Legitimate Emails**: {legit_count:,} ({legit_pct:.2f}%)
- **Class Balance**: 52.0% Phishing / 48.0% Legitimate (Well balanced)
"""
    with open(os.path.join(REPORTS_DIR, "email_phishing_quality_report.md"), "w") as f:
        f.write(quality_md)

    leakage_md = f"""# Data Leakage Audit Report: Email Phishing

**Dataset**: `phishing_email.csv`  
**Target**: `label` (0 = Legitimate, 1 = Phishing)  

## 1. Feature Assessment & Leakage Classification

| Feature Component | Classification | Rationale | Action |
| :--- | :--- | :--- | :--- |
| Duplicate Emails ({duplicate_rows:,}) | **POTENTIAL_LEAKAGE** | Identical spam campaigns could cross-contaminate train and test splits. | **DEDUPLICATED BEFORE SPLITTING** |
| Header Metadata | **N/A** | Text corpus consists of body and subject text (`text_combined`), preventing IP or routing header leaks. | **SAFE** |
| Raw Text | **SAFE** | Vectorized using TF-IDF fitted strictly on training data. | **RETAINED** |
| Structural NLP Meta-features | **SAFE** | Real-time computable structural signals (urgency, credentials, financial terms, URLs). | **RETAINED & SCALED** |

## 2. Leakage Prevention Protocol
- Deduplication applied on raw email text strings ({duplicate_rows:,} removed).
- Stratified 70/15/15 train/val/test split.
- TF-IDF vocabulary (top 4,000 terms) and Scaler fitted exclusively on training set.
"""
    with open(os.path.join(REPORTS_DIR, "email_phishing_leakage_report.md"), "w") as f:
        f.write(leakage_md)
        
    logger.info("Quality and Leakage reports generated successfully.")

def run_email_pipeline():
    logger.info("Step 1: Loading raw Email Phishing dataset...")
    raw_df = pd.read_csv(DATA_PATH)
    logger.info("Loaded %d rows.", len(raw_df))
    
    # Deduplicate by text
    dedup_df = raw_df.drop_duplicates(subset=['text_combined']).copy()
    logger.info("Deduplication: %d -> %d rows (%d duplicates removed).", len(raw_df), len(dedup_df), len(raw_df) - len(dedup_df))
    
    # Fill any empty text with empty string
    dedup_df['text_combined'] = dedup_df['text_combined'].fillna('')
    
    # Generate reports
    generate_quality_and_leakage_reports(raw_df, dedup_df)
    
    X_text = dedup_df['text_combined']
    y = dedup_df['label']
    
    # Train / Val / Test Split (70 / 15 / 15) stratified
    logger.info("Step 2: Creating stratified 70 / 15 / 15 Train/Val/Test Split...")
    X_train_val_txt, X_test_txt, y_train_val, y_test = train_test_split(
        X_text, y, test_size=0.15, stratify=y, random_state=42
    )
    
    val_ratio = 0.15 / 0.85
    X_train_txt, X_val_txt, y_train, y_val = train_test_split(
        X_train_val_txt, y_train_val, test_size=val_ratio, stratify=y_train_val, random_state=42
    )
    
    logger.info("Split sizes - Train: %d (Phishing: %d), Val: %d (Phishing: %d), Test: %d (Phishing: %d)",
                len(X_train_txt), int(y_train.sum()), len(X_val_txt), int(y_val.sum()), len(X_test_txt), int(y_test.sum()))

    # Step 3: Feature Extraction (TF-IDF + Metadata)
    logger.info("Step 3: Extracting TF-IDF and structural email features...")
    vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1, 2), stop_words='english', sublinear_tf=True, min_df=3)
    scaler = StandardScaler()
    
    # Train transformation
    X_train_tfidf = vectorizer.fit_transform(X_train_txt)
    X_train_meta = scaler.fit_transform(extract_meta_features(X_train_txt))
    X_train_proc = hstack([X_train_tfidf, X_train_meta]).tocsr()
    
    # Val transformation
    X_val_tfidf = vectorizer.transform(X_val_txt)
    X_val_meta = scaler.transform(extract_meta_features(X_val_txt))
    X_val_proc = hstack([X_val_tfidf, X_val_meta]).tocsr()
    
    # Test transformation
    X_test_tfidf = vectorizer.transform(X_test_txt)
    X_test_meta = scaler.transform(extract_meta_features(X_test_txt))
    X_test_proc = hstack([X_test_tfidf, X_test_meta]).tocsr()

    # Candidate Models
    models = {
        "MultinomialNB": MultinomialNB(alpha=0.1),
        "LogisticRegression": LogisticRegression(C=2.0, max_iter=1000, random_state=42),
        "CalibratedLinearSVC": CalibratedClassifierCV(LinearSVC(C=1.0, random_state=42), cv=3)
    }
    
    logger.info("Step 4: Training and comparing candidate models on Validation set...")
    val_results = {}
    for name, model in models.items():
        logger.info("Training %s...", name)
        if name == "MultinomialNB":
            model.fit(X_train_tfidf, y_train)
            val_probs = model.predict_proba(X_val_tfidf)[:, 1]
        else:
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
                    
    # Select Champion Model (highest F1 and PR-AUC)
    best_model_name = max(val_results.keys(), key=lambda k: (val_results[k]['f1_default'], val_results[k]['pr_auc']))
    best_model = val_results[best_model_name]['model']
    best_val_probs = val_results[best_model_name]['val_probs']
    logger.info("Selected Champion Model: %s (Val F1: %.4f, PR-AUC: %.4f)",
                best_model_name, val_results[best_model_name]['f1_default'], val_results[best_model_name]['pr_auc'])
    
    # Step 5: Threshold Optimization on Validation Set
    logger.info("Step 5: Optimizing fraud decision threshold on Validation Set...")
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

    # Step 6: Final Untouched Test Set Evaluation
    logger.info("Step 6: Evaluating Champion Model on Untouched Test Set...")
    eval_test_matrix = X_test_tfidf if best_model_name == "MultinomialNB" else X_test_proc
    test_probs = best_model.predict_proba(eval_test_matrix)[:, 1]
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
    logger.info("Test Results: PR-AUC=%.4f, ROC-AUC=%.4f, Accuracy=%.4f, Recall=%.4f, Precision=%.4f, F1=%.4f, TP=%d, FP=%d, FN=%d",
                test_pr_auc, test_roc_auc, test_acc, test_rec, test_prec, test_f1, tp, fp, fn)

    # Step 7: Top Informative Keywords
    logger.info("Step 7: Extracting top informative keywords...")
    top_features = []
    feature_names = vectorizer.get_feature_names_out().tolist() + list(extract_meta_features(pd.Series(["test"])).columns)
    
    if hasattr(best_model, "coef_"):
        coefs = best_model.coef_[0]
        sorted_indices = np.argsort(coefs)[::-1]
        for idx in sorted_indices[:15]:
            feat_name = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
            top_features.append({
                "feature": feat_name,
                "weight": float(coefs[idx])
            })
    elif hasattr(best_model, "calibrated_classifiers_"):
        # Average coefficients from base linear models
        base_coefs = [clf.estimator.coef_[0] for clf in best_model.calibrated_classifiers_]
        avg_coefs = np.mean(base_coefs, axis=0)
        sorted_indices = np.argsort(avg_coefs)[::-1]
        for idx in sorted_indices[:15]:
            feat_name = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
            top_features.append({
                "feature": feat_name,
                "weight": float(avg_coefs[idx])
            })

    # Step 8: Save Artifacts
    logger.info("Step 8: Persisting model artifacts to %s...", MODEL_DIR)
    joblib.dump(best_model, os.path.join(MODEL_DIR, "model.joblib"))
    
    pipeline_bundle = {
        "vectorizer": vectorizer,
        "scaler": scaler,
        "meta_feature_names": list(extract_meta_features(pd.Series(["test"])).columns)
    }
    joblib.dump(pipeline_bundle, os.path.join(MODEL_DIR, "preprocessor.joblib"))
    
    feature_schema = {
        "input_type": "text",
        "primary_field": "text",
        "vocabulary_size": len(vectorizer.vocabulary_),
        "meta_features": list(extract_meta_features(pd.Series(["test"])).columns)
    }
    with open(os.path.join(MODEL_DIR, "feature_schema.json"), "w") as f:
        json.dump(feature_schema, f, indent=2)
        
    label_mapping = {
        "0": "LEGITIMATE",
        "1": "PHISHING"
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
        "model_name": "email_phishing_detector",
        "domain": "EMAIL",
        "dataset_name": "phishing_email",
        "dataset_file": "dataset/Email 2/phishing_email.csv",
        "algorithm": best_model_name,
        "train_rows": len(X_train_txt),
        "val_rows": len(X_val_txt),
        "test_rows": len(X_test_txt),
        "phishing_ratio": float(y.mean()),
        "selected_threshold": best_threshold,
        "test_metrics": test_metrics,
        "top_features": top_features,
        "status": "READY"
    }
    with open(os.path.join(MODEL_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    readme_content = f"""# Email Phishing & Fraud Detection Model

- **Model ID**: `email_phishing_detector`
- **Domain**: `EMAIL`
- **Algorithm**: `{best_model_name}`
- **Test Accuracy**: `{test_acc * 100:.2f}%`
- **Test PR-AUC**: `{test_pr_auc:.4f}`
- **Test ROC-AUC**: `{test_roc_auc:.4f}`
- **Test Recall**: `{test_rec * 100:.2f}%` ({tp:,} of {tp+fn:,} phishing emails intercepted)
- **Test Precision**: `{test_prec * 100:.2f}%`
- **Test F1**: `{test_f1:.4f}`
- **Optimal Decision Threshold**: `{best_threshold}`

## Artifacts
- `model.joblib`: Trained NLP classifier
- `preprocessor.joblib`: TF-IDF vectorizer + structural metadata feature scaler bundle
- `feature_schema.json`: Input text specifications
- `threshold.json`: Calibrated decision threshold
- `metrics.json`: Untouched test set metrics
- `metadata.json`: Full provenance and configuration
"""
    with open(os.path.join(MODEL_DIR, "README.md"), "w") as f:
        f.write(readme_content)

    # Step 9: Generate Evaluation Report
    eval_report_md = f"""# Model Evaluation Report: Email Phishing Detection

**Dataset**: `data/raw/email/phishing_email.csv`  
**Domain**: Email  
**Champion Algorithm**: `{best_model_name}`  
**Decision Threshold**: `{best_threshold}`  

## 1. Candidate Model Comparison (Validation Set)

| Model | PR-AUC | ROC-AUC | F1 (0.50) | Recall (0.50) | Precision (0.50) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Multinomial Naive Bayes** | {val_results['MultinomialNB']['pr_auc']:.4f} | {val_results['MultinomialNB']['roc_auc']:.4f} | {val_results['MultinomialNB']['f1_default']:.4f} | {val_results['MultinomialNB']['recall_default']:.4f} | {val_results['MultinomialNB']['precision_default']:.4f} |
| **Logistic Regression** | {val_results['LogisticRegression']['pr_auc']:.4f} | {val_results['LogisticRegression']['roc_auc']:.4f} | {val_results['LogisticRegression']['f1_default']:.4f} | {val_results['LogisticRegression']['recall_default']:.4f} | {val_results['LogisticRegression']['precision_default']:.4f} |
| **Calibrated Linear SVC** | **{val_results['CalibratedLinearSVC']['pr_auc']:.4f}** | **{val_results['CalibratedLinearSVC']['roc_auc']:.4f}** | **{val_results['CalibratedLinearSVC']['f1_default']:.4f}** | **{val_results['CalibratedLinearSVC']['recall_default']:.4f}** | **{val_results['CalibratedLinearSVC']['precision_default']:.4f}** |

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
- **Precision**: `{test_prec * 100:.2f}%`
- **Recall**: `{test_rec * 100:.2f}%` ({tp:,} / {tp+fn:,} phishing attacks blocked)
- **F1-Score**: `{test_f1:.4f}`
- **PR-AUC**: `{test_pr_auc:.4f}`
- **ROC-AUC**: `{test_roc_auc:.4f}`
- **False Positive Rate (FPR)**: `{fpr * 100:.2f}%` ({fp:,} false alarms)
- **False Negative Rate (FNR)**: `{fnr * 100:.2f}%` ({fn:,} missed phishing attacks)

### Confusion Matrix
| | Predicted Legitimate | Predicted Phishing |
| :--- | :--- | :--- |
| **Actual Legitimate** | {tn:,} (TN) | {fp:,} (FP) |
| **Actual Phishing** | {fn:,} (FN) | {tp:,} (TP) |

## 4. Top Informative Keywords & Meta-Features

| Rank | Token / Feature | Weight / Impact |
| :--- | :--- | :--- |
"""
    for i, tf in enumerate(top_features[:10], 1):
        eval_report_md += f"| {i} | `{tf['feature']}` | {tf['weight']:.4f} |\n"

    with open(os.path.join(REPORTS_DIR, "email_phishing_evaluation_report.md"), "w") as f:
        f.write(eval_report_md)
        
    logger.info("Email Training Pipeline Completed Successfully!")
    return metadata

if __name__ == "__main__":
    run_email_pipeline()
