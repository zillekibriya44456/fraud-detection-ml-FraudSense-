# Current Audit and Database Architecture (Pre-Step 5)

## 1. Database Infrastructure
- **Engine**: SQLite
- **Location**: `data/audit_log.db`
- **ORM**: SQLAlchemy (defined in `database/models.py`)

## 2. Existing Tables

### A. `transaction_audit_logs`
Logs every single prediction event.
- **Fields**:
  - `id` (Primary Key, integer)
  - `timestamp`
  - Input Features: `step`, `type`, `amount`, `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest`
  - Model Outputs: `prediction`, `fraud_probability`, `risk_level`, `recommended_action`, `decision_policy`, `model_version`, `inference_latency_ms`
- **Notes**: It serves as an immutable log of the API input and the ML/Decision Engine output.

### B. `fraud_alerts`
Logs a subset of transactions.
- **Fields**:
  - `id` (Primary Key, integer)
  - `timestamp`
  - `transaction_id` (String, index)
  - `audit_log_id` (Integer)
  - `risk_level`, `fraud_probability`, `recommended_action`, `model_version`
- **Notes**: Currently, `api/routes.py` hardcodes an insert into this table *if* `risk_level == "HIGH"`. 

## 3. Relationships and Identifiers
- `FraudAlert.audit_log_id` maps back to `TransactionAuditLog.id`.
- The system currently expects the client to pass an optional `transaction_id` in the JSON body. If not passed, it defaults to `"TX_000"` in `api/routes.py`, which is a **massive deduplication risk**. Every case currently without an explicit ID gets lumped as `"TX_000"`.

## 4. Current Limitations
- **No State Machine**: `FraudAlert` is just an append-only log. There is no `status` (e.g., OPEN, RESOLVED).
- **No Analyst Workflow**: No fields for analyst notes, resolution timestamps, or assignments.
- **Hardcoded Policy**: The rule `if risk_level == "HIGH"` is hardcoded directly into the API endpoint instead of a configurable policy.
- **Deduplication Risk**: If the same transaction is scored twice (e.g., retry logic), it will insert two identical audit logs and two identical fraud alerts.
- **Concurrency**: SQLite handles concurrent reads well, but concurrent writes will lock the database. At production scale, this will bottleneck the prediction API if case creation holds the write lock.
