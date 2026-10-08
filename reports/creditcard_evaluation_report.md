# Model Evaluation Report: Credit Card Fraud Detection

**Dataset**: `data/raw/card/creditcard.csv`  
**Domain**: Card  
**Champion Algorithm**: `XGBoost`  
**Decision Threshold**: `0.95`  

## 1. Candidate Model Comparison (Validation Set)

| Model | PR-AUC | ROC-AUC | F1 (0.50) | Recall (0.50) | Precision (0.50) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression** | 0.7115 | 0.9777 | 0.1117 | 0.9155 | 0.0595 |
| **Random Forest** | 0.7728 | 0.9814 | 0.8356 | 0.8592 | 0.8133 |
| **XGBoost (Champion)** | **0.8599** | **0.9784** | **0.8333** | **0.8451** | **0.8219** |

## 2. Threshold Calibration Analysis (Validation Set)

| Threshold | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- |
| `0.05` | 0.1950 | 0.8732 | 0.3188 |
| `0.1` | 0.3315 | 0.8592 | 0.4784 |
| `0.15` | 0.4511 | 0.8451 | 0.5882 |
| `0.2` | 0.5357 | 0.8451 | 0.6557 |
| `0.25` | 0.5660 | 0.8451 | 0.6780 |
| `0.3` | 0.6522 | 0.8451 | 0.7362 |
| `0.35` | 0.7059 | 0.8451 | 0.7692 |
| `0.4` | 0.7229 | 0.8451 | 0.7792 |
| `0.45` | 0.7500 | 0.8451 | 0.7947 |
| `0.5` | 0.8219 | 0.8451 | 0.8333 |
| `0.55` | 0.8333 | 0.8451 | 0.8392 |
| `0.6` | 0.8571 | 0.8451 | 0.8511 |
| `0.65` | 0.8551 | 0.8310 | 0.8429 |
| `0.7` | 0.8806 | 0.8310 | 0.8551 |
| `0.75` | 0.8806 | 0.8310 | 0.8551 |
| `0.8` | 0.8939 | 0.8310 | 0.8613 |
| `0.85` | 0.9365 | 0.8310 | 0.8806 |
| `0.9` | 0.9365 | 0.8310 | 0.8806 |
| `0.95` | 0.9667 | 0.8169 | 0.8855 **(Selected)** |

## 3. Untouched Test Set Performance

- **Accuracy**: `99.95%`
- **Precision**: `0.9623`
- **Recall**: `0.7183` (51 / 71 frauds detected)
- **F1-Score**: `0.8226`
- **PR-AUC**: `0.8096`
- **ROC-AUC**: `0.9656`
- **False Positive Rate (FPR)**: `0.000047` (2 false alarms)
- **False Negative Rate (FNR)**: `0.2817` (20 missed frauds)

### Confusion Matrix
| | Predicted Legitimate | Predicted Fraud |
| :--- | :--- | :--- |
| **Actual Legitimate** | 42,486 (TN) | 2 (FP) |
| **Actual Fraud** | 20 (FN) | 51 (TP) |

## 4. Top Explainability Features (TreeSHAP)

| Rank | Feature Name | Impact / Importance |
| :--- | :--- | :--- |
| 1 | `V14` | 1.7255 |
| 2 | `V4` | 1.2345 |
| 3 | `V12` | 0.7283 |
| 4 | `V11` | 0.6379 |
| 5 | `V10` | 0.4827 |
| 6 | `V3` | 0.3875 |
| 7 | `V5` | 0.3163 |
| 8 | `V19` | 0.2778 |
| 9 | `V26` | 0.2550 |
| 10 | `V28` | 0.2270 |
