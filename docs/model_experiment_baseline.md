# Model Experiment Baseline Analysis

## 1. Dataset
- **Name**: PaySim (`PS_20174392719_1491204439457_log.csv`)
- **Filters**: Currently filtered to only include `TRANSFER` and `CASH_OUT` transactions, as fraud exclusively occurs in these categories in PaySim.

## 2. Features Evaluated
- **Included Numerical**: `amount`, `oldbalanceOrg`, `oldbalanceDest`, and generated behavioral/velocity features.
- **Included Categorical**: `type`.
- **Excluded Features**: `nameOrig`, `nameDest` (high cardinality), `isFlaggedFraud` (synthetic business rule).
- **Pre-Authorization Constraints**: `newbalanceOrig` and `newbalanceDest` are strictly removed to prevent post-transaction data leakage.

## 3. Train/Validation/Test Methodology (Current Split Risks)
- **Current Approach**: A random `train_test_split` with `stratify=y` (Train: 70%, Val: 15%, Test: 15%).
- **Risks**: Random splits in financial fraud are prone to **temporal leakage**. If a fraud ring operates over a 3-day period, randomly splitting means the model might train on day 2 and predict on day 1, effectively "peeking" into the future. 
- **Alternative for Experiments**: We will implement a *temporal split* (e.g., train on first 70% of time steps, test on last 30%) in our experimental scripts, while leaving the existing `train.py` untouched to avoid breaking the prototype.

## 4. Class Imbalance Methodology
- **Current Approach**: Uses XGBoost's built-in `scale_pos_weight` (Ratio of negative to positive class counts). No manual oversampling (SMOTE) or undersampling is performed.

## 5. Existing XGBoost Configuration
- `n_estimators=100`
- `max_depth=5`
- `learning_rate=0.1`
- `eval_metric='logloss'`

## 6. Existing Evaluation Methodology
- **Threshold**: Currently fixed at 0.5 (via `.predict()`).
- **Metrics**: Precision, Recall, F1-Score, ROC-AUC, PR-AUC. Confusion matrix and PR curves are plotted. No explicit threshold optimization is performed.
