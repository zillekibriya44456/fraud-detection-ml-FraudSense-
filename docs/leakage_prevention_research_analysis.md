# Leakage Prevention Research Analysis

## 1. The Post-Transaction Leakage Problem
In fraud detection research, datasets often contain features that represent the *state of an account after a transaction has completed*. 

In the PaySim dataset, these features are:
- `newbalanceOrig`: The sender's balance after the transaction.
- `newbalanceDest`: The receiver's balance after the transaction.

### Why is this leakage?
A real-time fraud API evaluates a transaction **before** it is authorized. The new balances do not exist yet. If a machine learning model is trained on `newbalanceOrig`, it learns a synthetic mathematical rule (e.g., `oldbalanceOrig - amount == newbalanceOrig`), which creates a near-perfect (but practically useless) F1-score.

## 2. Project Implementation
FRAUDSENSE AI solves this strictly at the API and Training layers.

### Feature Exclusion
- The `src/preprocessing.py` script explicitly drops `newbalanceOrig` and `newbalanceDest` prior to model training.

### API Validation (Pydantic)
- The FastAPI endpoint uses a strict Pydantic schema (`TransactionRequest`). 
- Any API client attempting to inject `newbalanceOrig` into the payload will have it stripped or rejected before it ever reaches the `predict_fraud` function.
- This creates an **air-gap** that guarantees the pre-authorization constraint is respected in production.

## 3. Research Implication
By removing these leaking features, the model's F1-score is more realistic. The system evaluates the transaction based entirely on historical state (`oldbalanceOrg`), the current transaction `amount`, and behavioral velocity.
