# Model Evaluation Report: SMS Spam & Scam Detection

**Dataset**: `data/raw/sms/SMSSpamCollection`  
**Domain**: SMS  
**Champion Algorithm**: `CalibratedLinearSVC`  
**Decision Threshold**: `0.4`  

## 1. Candidate Model Comparison (Validation Set)

| Model | PR-AUC | ROC-AUC | F1 (0.50) | Recall (0.50) | Precision (0.50) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Multinomial Naive Bayes** | 0.9594 | 0.9842 | 0.9000 | 0.8265 | 0.9878 |
| **Logistic Regression** | 0.9845 | 0.9967 | 0.9524 | 0.9184 | 0.9890 |
| **Calibrated Linear SVC** | **0.9878** | **0.9973** | **0.9574** | **0.9184** | **1.0000** |

## 2. Threshold Calibration Analysis (Validation Set)

| Threshold | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- |
| `0.05` | 0.7559 | 0.9796 | 0.8533 |
| `0.1` | 0.9048 | 0.9694 | 0.9360 |
| `0.15` | 0.9495 | 0.9592 | 0.9543 |
| `0.2` | 0.9787 | 0.9388 | 0.9583 |
| `0.25` | 0.9787 | 0.9388 | 0.9583 |
| `0.3` | 0.9892 | 0.9388 | 0.9634 |
| `0.35` | 0.9892 | 0.9388 | 0.9634 |
| `0.4` | 1.0000 | 0.9388 | 0.9684 **(Selected)** |
| `0.45` | 1.0000 | 0.9388 | 0.9684 |
| `0.5` | 1.0000 | 0.9184 | 0.9574 |
| `0.55` | 1.0000 | 0.9082 | 0.9519 |
| `0.6` | 1.0000 | 0.9082 | 0.9519 |
| `0.65` | 1.0000 | 0.8980 | 0.9462 |
| `0.7` | 1.0000 | 0.8776 | 0.9348 |
| `0.75` | 1.0000 | 0.8469 | 0.9171 |
| `0.8` | 1.0000 | 0.8265 | 0.9050 |
| `0.85` | 1.0000 | 0.7857 | 0.8800 |
| `0.9` | 1.0000 | 0.7857 | 0.8800 |
| `0.95` | 1.0000 | 0.7551 | 0.8605 |

## 3. Untouched Test Set Performance

- **Accuracy**: `98.97%`
- **Precision**: `97.87%`
- **Recall**: `93.88%` (92 / 98 scam attacks blocked)
- **F1-Score**: `0.9583`
- **PR-AUC**: `0.9826`
- **ROC-AUC**: `0.9950`
- **False Positive Rate (FPR)**: `0.29%` (2 false alarms)
- **False Negative Rate (FNR)**: `6.12%` (6 missed scams)

### Confusion Matrix
| | Predicted Legitimate | Predicted Scam |
| :--- | :--- | :--- |
| **Actual Legitimate** | 676 (TN) | 2 (FP) |
| **Actual Scam** | 6 (FN) | 92 (TP) |

## 4. Top Informative Keywords & Meta-Features

| Rank | Token / Feature | Weight / Impact |
| :--- | :--- | :--- |
