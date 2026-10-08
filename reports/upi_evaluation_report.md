# Model Evaluation Report: UPI Fraud Detection

**Dataset**: `dataset/upi_transactions_2024.csv`
**Domain**: UPI
**Champion Algorithm**: `XGBoost` + IsolationForest Anomaly Augmentation
**Decision Threshold**: `0.4`

> **Data Quality Note**: Statistical tests show near-zero correlation between features
> and fraud labels (quasi-random assignment in this synthetic dataset).

## 1. Candidate Model Comparison (Validation Set)

| Model | PR-AUC | ROC-AUC | F1 (0.50) | Recall (0.50) | Precision (0.50) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression** | 0.0024 | 0.5649 | 0.0046 | 0.5139 | 0.0023 |
| **Random Forest** | 0.0017 | 0.4627 | 0.0000 | 0.0000 | 0.0000 |
| **XGBoost (Champion)** | **0.0026** | **0.5671** | **0.0046** | **0.0833** | **0.0024** |

## 2. Threshold Calibration Analysis (Validation Set)

| Threshold | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- |
| `0.01` | 0.0019 | 1.0000 | 0.0038 |
| `0.02` | 0.0019 | 0.9861 | 0.0038 |
| `0.03` | 0.0019 | 0.9722 | 0.0038 |
| `0.04` | 0.0020 | 0.9722 | 0.0039 |
| `0.05` | 0.0020 | 0.9583 | 0.0040 |
| `0.06` | 0.0019 | 0.9028 | 0.0039 |
| `0.07` | 0.0020 | 0.8750 | 0.0039 |
| `0.08` | 0.0020 | 0.8611 | 0.0040 |
| `0.09` | 0.0020 | 0.8333 | 0.0040 |
| `0.1` | 0.0020 | 0.8056 | 0.0041 |
| `0.1` | 0.0020 | 0.8056 | 0.0041 |
| `0.15` | 0.0022 | 0.6806 | 0.0043 |
| `0.2` | 0.0023 | 0.5556 | 0.0045 |
| `0.25` | 0.0026 | 0.4861 | 0.0052 |
| `0.3` | 0.0027 | 0.3750 | 0.0054 |
| `0.35` | 0.0029 | 0.2917 | 0.0057 |
| `0.4` | 0.0036 | 0.2639 | 0.0071 **(Selected)** |
| `0.45` | 0.0030 | 0.1528 | 0.0058 |
| `0.5` | 0.0024 | 0.0833 | 0.0046 |
| `0.5` | 0.0024 | 0.0833 | 0.0046 |
| `0.55` | 0.0024 | 0.0556 | 0.0046 |
| `0.6` | 0.0029 | 0.0417 | 0.0054 |
| `0.65` | 0.0033 | 0.0278 | 0.0059 |
| `0.7` | 0.0031 | 0.0139 | 0.0051 |
| `0.75` | 0.0000 | 0.0000 | 0.0000 |
| `0.8` | 0.0000 | 0.0000 | 0.0000 |
| `0.85` | 0.0000 | 0.0000 | 0.0000 |
| `0.9` | 0.0000 | 0.0000 | 0.0000 |
| `0.95` | 0.0000 | 0.0000 | 0.0000 |

## 3. Untouched Test Set Performance

- **Accuracy**: `85.51%`
- **Precision**: `0.0013`
- **Recall**: `0.0972`
- **F1-Score**: `0.0026`
- **PR-AUC**: `0.0018`
- **ROC-AUC**: `0.4792`
- **False Positive Rate (FPR)**: `0.1435` (5,370 false alarms)
- **False Negative Rate (FNR)**: `0.9028` (65 missed frauds)

### Confusion Matrix
| | Predicted Legitimate | Predicted Fraud |
| :--- | :--- | :--- |
| **Actual Legitimate** | 32,058 (TN) | 5,370 (FP) |
| **Actual Fraud** | 65 (FN) | 7 (TP) |

## 4. Top Explainability Features (TreeSHAP)

| Rank | Feature Name | Mean Absolute SHAP Impact |
| :--- | :--- | :--- |
| 1 | `isolation_forest_score` | 0.2214 |
| 2 | `sender_state_Uttar Pradesh` | 0.2155 |
| 3 | `sender_bank_SBI` | 0.2075 |
| 4 | `sender_state_Tamil Nadu` | 0.2062 |
| 5 | `sender_state_Maharashtra` | 0.1956 |
| 6 | `amount (INR)` | 0.1866 |
| 7 | `log_amount` | 0.1802 |
| 8 | `sender_state_Karnataka` | 0.1760 |
| 9 | `receiver_bank_SBI` | 0.1504 |
| 10 | `hour_of_day` | 0.1473 |
