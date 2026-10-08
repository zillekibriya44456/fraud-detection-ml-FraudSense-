# Model Evaluation Report: Email Phishing Detection

**Dataset**: `data/raw/email/phishing_email.csv`  
**Domain**: Email  
**Champion Algorithm**: `CalibratedLinearSVC`  
**Decision Threshold**: `0.5`  

## 1. Candidate Model Comparison (Validation Set)

| Model | PR-AUC | ROC-AUC | F1 (0.50) | Recall (0.50) | Precision (0.50) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Multinomial Naive Bayes** | 0.9937 | 0.9939 | 0.9463 | 0.9093 | 0.9865 |
| **Logistic Regression** | 0.9979 | 0.9980 | 0.9832 | 0.9858 | 0.9805 |
| **Calibrated Linear SVC** | **0.9983** | **0.9983** | **0.9842** | **0.9866** | **0.9819** |

## 2. Threshold Calibration Analysis (Validation Set)

| Threshold | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- |
| `0.05` | 0.9258 | 0.9983 | 0.9607 |
| `0.1` | 0.9439 | 0.9975 | 0.9700 |
| `0.15` | 0.9554 | 0.9960 | 0.9752 |
| `0.2` | 0.9624 | 0.9946 | 0.9782 |
| `0.25` | 0.9673 | 0.9930 | 0.9800 |
| `0.3` | 0.9721 | 0.9925 | 0.9822 |
| `0.35` | 0.9748 | 0.9921 | 0.9833 |
| `0.4` | 0.9768 | 0.9904 | 0.9835 |
| `0.45` | 0.9793 | 0.9880 | 0.9837 |
| `0.5` | 0.9819 | 0.9866 | 0.9842 **(Selected)** |
| `0.55` | 0.9832 | 0.9830 | 0.9831 |
| `0.6` | 0.9852 | 0.9812 | 0.9832 |
| `0.65` | 0.9877 | 0.9778 | 0.9827 |
| `0.7` | 0.9886 | 0.9721 | 0.9803 |
| `0.75` | 0.9901 | 0.9675 | 0.9787 |
| `0.8` | 0.9915 | 0.9627 | 0.9769 |
| `0.85` | 0.9929 | 0.9539 | 0.9730 |
| `0.9` | 0.9949 | 0.9417 | 0.9675 |
| `0.95` | 0.9975 | 0.9136 | 0.9537 |

## 3. Untouched Test Set Performance

- **Accuracy**: `98.35%`
- **Precision**: `98.28%`
- **Recall**: `98.57%` (6,335 / 6,427 phishing attacks blocked)
- **F1-Score**: `0.9842`
- **PR-AUC**: `0.9983`
- **ROC-AUC**: `0.9981`
- **False Positive Rate (FPR)**: `1.89%` (111 false alarms)
- **False Negative Rate (FNR)**: `1.43%` (92 missed phishing attacks)

### Confusion Matrix
| | Predicted Legitimate | Predicted Phishing |
| :--- | :--- | :--- |
| **Actual Legitimate** | 5,774 (TN) | 111 (FP) |
| **Actual Phishing** | 92 (FN) | 6,335 (TP) |

## 4. Top Informative Keywords & Meta-Features

| Rank | Token / Feature | Weight / Impact |
| :--- | :--- | :--- |
| 1 | `josemonkeyorg` | 3.5664 |
| 2 | `2004` | 2.8470 |
| 3 | `2005` | 2.5556 |
| 4 | `gr` | 2.1790 |
| 5 | `remove` | 2.1032 |
| 6 | `0300` | 2.0787 |
| 7 | `investment` | 1.9984 |
| 8 | `click` | 1.9351 |
| 9 | `http` | 1.8090 |
| 10 | `com` | 1.7183 |
