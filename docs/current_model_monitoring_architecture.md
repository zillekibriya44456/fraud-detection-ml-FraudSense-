# Current Model Monitoring Architecture (Pre-Step 6)

## 1. Current Model Version
- **Model Type**: XGBoost Classifier (`v2_pre_auth` as referenced in API schemas)
- **Status**: ACTIVE

## 2. Model Artifact Locations
- **Model**: `models/xgboost_fraud_model.json`
- **Preprocessor**: `models/preprocessor.joblib`
- **Metrics (Past)**: `artifacts/metrics/model_comparison.json`

## 3. Feature Schema Version
- **Version**: `v1.0` (as defined in `TransactionResponse` schema)
- **Features Used**: `step`, `type`, `amount`, `oldbalanceOrg`, `oldbalanceDest` (along with engineered behavioral features, but post-transaction balances are explicitly excluded for inference).

## 4. Training Dataset
- **Location**: `data/raw/PS_20174392719_1491204439457_log.csv` (PaySim dataset)
- **Training Script**: `src/train.py`
- **Class Imbalance**: Handled via `scale_pos_weight`.

## 5. Training Date
- Unrecorded in the model artifact itself (currently missing a formal Model Registry).

## 6. Evaluation Metrics Available
- During training, `src/evaluate.py` generates metrics like Precision, Recall, F1, LogLoss.
- Stored temporarily in `model_comparison.json`.
- **Limitation**: No LIVE post-deployment performance metrics are tracked because fraud labels (ground truth) are delayed in the real world.

## 7. Baseline Feature Distributions Available
- **None**. The system currently does not compute or store any baseline statistics (e.g., mean, median, PSI) from the training data for the purpose of drift monitoring.

## 8. Current Limitations
- **No Drift Detection**: The system cannot detect if the live transactions look fundamentally different from the training data (Feature Drift).
- **No Prediction Drift**: The system cannot detect if the model suddenly starts predicting 50% of transactions as fraud instead of the expected 0.1% (Prediction Drift).
- **No Feedback Loop**: The system creates cases (Step 5), but there is no mechanism to take the analyst's resolution (`CONFIRMED_FRAUD`, `FALSE_POSITIVE`) and feed it back to evaluate live model performance.
- **No Retraining Strategy**: There is no logic to recommend when the model should be retrained based on drift or performance degradation.
