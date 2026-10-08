# Model Evaluation Report: URL Phishing Detection

**Dataset**: `data/raw/url_phishing/PhiUSIIL_Phishing_URL_Dataset.csv`  
**Domain**: URL Phishing  
**Champion Algorithm**: `RandomForest`  
**Decision Threshold**: `0.4`  

## 1. Candidate Model Comparison (Validation Set)

| Model | PR-AUC | ROC-AUC | F1 (0.50) | Recall (0.50) | Precision (0.50) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Random Forest** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **XGBoost (Champion)** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |

## 2. Threshold Calibration Analysis (Validation Set)

| Threshold | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- |
| `0.05` | 0.9967 | 1.0000 | 0.9983 |
| `0.1` | 0.9993 | 1.0000 | 0.9996 |
| `0.15` | 0.9997 | 1.0000 | 0.9999 |
| `0.2` | 0.9998 | 1.0000 | 0.9999 |
| `0.25` | 1.0000 | 1.0000 | 1.0000 |
| `0.3` | 1.0000 | 1.0000 | 1.0000 |
| `0.35` | 1.0000 | 1.0000 | 1.0000 |
| `0.4` | 1.0000 | 1.0000 | 1.0000 **(Selected)** |
| `0.45` | 1.0000 | 1.0000 | 1.0000 |
| `0.5` | 1.0000 | 1.0000 | 1.0000 |
| `0.55` | 1.0000 | 1.0000 | 1.0000 |
| `0.6` | 1.0000 | 1.0000 | 1.0000 |
| `0.65` | 1.0000 | 1.0000 | 1.0000 |
| `0.7` | 1.0000 | 1.0000 | 1.0000 |
| `0.75` | 1.0000 | 1.0000 | 1.0000 |
| `0.8` | 1.0000 | 1.0000 | 1.0000 |
| `0.85` | 1.0000 | 1.0000 | 1.0000 |
| `0.9` | 1.0000 | 0.9996 | 0.9998 |
| `0.95` | 1.0000 | 0.9968 | 0.9984 |

## 3. Untouched Test Set Performance

- **Accuracy**: `100.00%`
- **Precision**: `100.00%`
- **Recall**: `100.00%` (20,228 / 20,228 phishing attacks blocked)
- **F1-Score**: `1.0000`
- **PR-AUC**: `1.0000`
- **ROC-AUC**: `1.0000`
- **False Positive Rate (FPR)**: `0.01%` (1 false alarms)
- **False Negative Rate (FNR)**: `0.00%` (0 missed attacks)

### Confusion Matrix
| | Predicted Legitimate | Predicted Phishing |
| :--- | :--- | :--- |
| **Actual Legitimate** | 15,077 (TN) | 1 (FP) |
| **Actual Phishing** | 0 (FN) | 20,228 (TP) |

## 4. Top Explainability Features (TreeSHAP)

| Rank | Feature Name | Impact / Importance |
| :--- | :--- | :--- |
| 1 | `URLSimilarityIndex` | 0.1854 |
| 2 | `NoOfExternalRef` | 0.1656 |
| 3 | `LineOfCode` | 0.1475 |
| 4 | `NoOfSelfRef` | 0.1106 |
| 5 | `NoOfImage` | 0.0829 |
| 6 | `NoOfJS` | 0.0705 |
| 7 | `HasSocialNet` | 0.0344 |
| 8 | `NoOfCSS` | 0.0322 |
| 9 | `HasCopyrightInfo` | 0.0248 |
| 10 | `IsHTTPS` | 0.0210 |
