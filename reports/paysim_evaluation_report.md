# Model Evaluation: PaySim Mobile Money Fraud

**Champion**: `RandomForest` | **Threshold**: `0.525`

## 1. Candidate Model Comparison (Validation Set)

| Model | PR-AUC | ROC-AUC | F1@0.5 | Recall@0.5 | Precision@0.5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression** | 0.7906 | 0.9941 | 0.1819 | 0.9813 | 0.1003 |
| **Random Forest** | 0.9959 | 0.9986 | 0.9972 | 0.9951 | 0.9992 |
| **XGBoost** | **0.9942** | **0.9996** | **0.9812** | **0.9951** | **0.9676** |

## 2. Test Set Performance

- **PR-AUC**: `0.9990`
- **ROC-AUC**: `0.9999`
- **Recall**: `0.9976`
- **Precision**: `0.9984`
- **F1**: `0.9980`
- **FPR**: `0.0000` (2 false alarms)
- **FNR**: `0.0024` (3 missed frauds)

### Confusion Matrix
| | Predicted Legit | Predicted Fraud |
| :--- | :--- | :--- |
| **Actual Legit** | 414,328 | 2 |
| **Actual Fraud** | 3 | 1,229 |

## 3. Top SHAP Features
| Rank | Feature | Mean |SHAP| |
| :--- | :--- | :--- |
