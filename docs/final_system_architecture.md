# Final System Architecture

## 1. Request Flow (Pre-Authorization)
The system analyzes transactions in real-time before payment networks authorize the transfer.

1. **USER / PAYMENT SYSTEM**: Initiates a transaction (e.g., Transfer, Payment).
2. **API REQUEST**: Fast-path entry into `api/routes.py` (`POST /predict`).
3. **INPUT VALIDATION**: Pydantic schema (`TransactionRequest`) strictly enforces required data types and rejects invalid payloads.
4. **FEATURE AVAILABILITY VALIDATION**: Enforces temporal isolation. Ensures post-transaction features (like `newbalanceOrig`) are NOT passed to the model, preventing data leakage.
5. **BEHAVIORAL ANALYSIS**: The `BehavioralEngine` fetches short-term transaction history (velocity) from the database to compute risk signals, handling cold-start users gracefully.
6. **ML FRAUD PREDICTION**: The XGBoost model (`v2_pre_auth`) calculates the raw `fraud_probability`.
7. **EXPLAINABILITY**: SHAP (TreeExplainer) computes the top contributing features for the decision.
8. **CONTEXT-AWARE DECISION ENGINE**: Fuses the raw ML probability, behavioral risk signal, and global thresholds to categorize the risk.
9. **APPROVE / VERIFY / BLOCK**:
    - **LOW RISK**: APPROVE
    - **MEDIUM RISK**: VERIFY (Simulated Step-Up Auth)
    - **HIGH RISK**: BLOCK
10. **ALERT / CASE MANAGEMENT**: If VERIFY or BLOCK, a `FraudCase` is generated in the SQLite database and deduplicated by `transaction_id`.
11. **AUDIT LOGGING**: The transaction metadata, prediction, and latency are permanently saved to `transaction_audit_logs`.
12. **MONITORING BUFFER**: Background queries routinely read the audit logs.
13. **MODEL DRIFT MONITORING**: `DriftAnalyzer` computes Population Stability Index (PSI) against the V1 baseline, and `PerformanceAnalyzer` joins logs with delayed Case Resolutions to measure live Precision.

## 2. Infrastructure Components
- **Backend API**: FastAPI (Synchronous ML inference).
- **Frontend**: Streamlit Dashboard for analysts.
- **Database**: SQLite (Prototype limitation).
- **ML Model**: XGBoost loaded in-memory via Joblib/JSON.
- **Containerization**: Docker & Docker Compose (`api` and `ui` services).
