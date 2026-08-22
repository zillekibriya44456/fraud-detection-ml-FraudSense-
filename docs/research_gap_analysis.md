# Research Gap Analysis

## 1. Post-Transaction Data Leakage in Academic Fraud Evaluation
- **The Gap**: A vast majority of literature utilizing the PaySim dataset trains models using `newbalanceOrig` and `newbalanceDest`. This constitutes temporal data leakage, as these balances are only finalized *after* a payment network authorizes the transaction.
- **Our Solution**: FRAUDSENSE AI strictly defines a **pre-authorization** constraint, enforcing it at the API layer via Pydantic schemas. 

## 2. Binary ML Classification vs. Operational Decision Workflows
- **The Gap**: Most papers evaluate models purely on binary metrics (Precision, Recall, F1). However, in production, a false positive (blocking a legitimate user) causes severe business friction. Academic models lack the middleware to handle "uncertainty" effectively.
- **Our Solution**: The `APPROVE / VERIFY / BLOCK` decision engine. Instead of blocking all transactions above a 0.5 threshold, the system routes medium-risk transactions to a simulated step-up verification (e.g., OTP), bridging the gap between ML probabilities and banking operations.

## 3. Lack of End-to-End MLOps Prototypes in Literature
- **The Gap**: Research often stops at the Jupyter Notebook stage. There is a lack of literature detailing how to integrate fraud models with Case Management systems and asynchronous Drift Monitoring.
- **Our Solution**: FRAUDSENSE AI provides a complete lifecycle prototype, including SQLite-backed case queues, SHAP explainability, and PSI-based drift tracking.

*(Note: LITERATURE VERIFICATION REQUIRED. Actual academic citations for these gaps must be inserted prior to publication.)*
