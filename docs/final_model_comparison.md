# Final Model Comparison

> [!CAUTION]
> **MISSING DATA**: The experimental models (Logistic Regression, Random Forest) were planned in Step 8 but not executed. Only the active XGBoost prototype model has available metrics from its initial `train.py` run. All other models are marked as `N/A`.

| MODEL | STATUS | PRECISION | RECALL | F1-SCORE | PR-AUC | ROC-AUC | FALSE POSITIVES | FALSE NEGATIVES | PREDICTION LATENCY |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **XGBoost (v2_pre_auth)** | **ACTIVE PROTOTYPE** | 0.88* | 0.85* | 0.86* | 0.90* | 0.98* | 12* | 14* | ~15 ms |
| **Logistic Regression** | EXPERIMENTAL | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| **Random Forest** | EXPERIMENTAL | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| **XGBoost (Temporal)** | EXPERIMENTAL | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

*\*Note: Metrics for the active prototype are estimates from the random-split `train.py` run in Step 1. A rigorous temporal split evaluation (Step 8) is required for publication-quality numbers.*
