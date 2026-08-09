# Dataset: PaySim (Mobile Money Transactions)

## 1. Overview
We have selected the **PaySim** dataset for this project. PaySim is a synthetic dataset based on a real mobile money transaction dataset from a multinational company operating in a major African country. 

## 2. Why PaySim?
- **Research Standard:** It is one of the most widely used datasets in academic literature for financial fraud.
- **Interpretable Features:** Unlike the Kaggle Credit Card dataset (which hides features behind PCA like `V1`, `V2`), PaySim provides clear, raw business features (e.g., `amount`, `oldbalanceOrg`). This is **critical** for our Phase 10 goal of Explainable AI (SHAP) and Phase 5 goal of Behavioral Feature Engineering.
- **Realistic Imbalance:** It models a realistic ratio of normal vs. fraudulent transactions, allowing us to deeply explore class-imbalance handling.

## 3. Data Dictionary
- `step`: Maps a unit of time in the real world (1 step = 1 hour). Total steps = 744 (31 days).
- `type`: Type of transaction (CASH-IN, CASH-OUT, DEBIT, PAYMENT, TRANSFER).
- `amount`: Amount of the transaction in local currency.
- `nameOrig`: Customer who started the transaction.
- `oldbalanceOrg`: Initial balance before the transaction.
- `newbalanceOrig`: New balance after the transaction.
- `nameDest`: Customer who is the recipient of the transaction.
- `oldbalanceDest`: Initial balance of recipient before the transaction.
- `newbalanceDest`: New balance of recipient after the transaction.
- `isFraud`: **(Target Variable)** Indicates if the transaction was made by a fraudulent agent.
- `isFlaggedFraud`: A simple business rule (transactions > 200,000) flagging illegal attempts. (We will likely drop or ignore this as our ML model will replace it).

## 4. Source
Kaggle: [PaySim1 dataset](https://www.kaggle.com/datasets/ealaxi/paysim1)