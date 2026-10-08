# Model Evaluation: Bitcoin Fraud

**Champion**: `XGBoost` | **Threshold**: `0.825`

## 1. Test Set Performance

- **PR-AUC**: `0.0451`
- **ROC-AUC**: `0.7053`
- **Recall**: `0.0178`
- **Precision**: `0.1071`
- **F1**: `0.0305`

### Confusion Matrix
| | Predicted Legit | Predicted Illicit |
| :--- | :--- | :--- |
| **Actual Legit** | 6,493 | 25 |
| **Actual Illicit** | 166 | 3 |
