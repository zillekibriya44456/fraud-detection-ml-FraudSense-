# Fraud Case Management Architecture

## 1. System Overview
The Fraud Case Management system transitions the application from a raw "transaction scoring API" into a mature investigation platform. Suspicious transactions (e.g., HIGH or MEDIUM risk) are converted into `FraudCase` records that security analysts can triage, investigate, and resolve.

## 2. Alert Generation Flow
```mermaid
graph TD
    A[API Request] --> B[XGBoost Predictor]
    B --> C[Behavioral Engine]
    C --> D[Context-Aware Decision Engine]
    D --> E[Case Manager (Alert Policy)]
    E -- "APPROVE" --> F[Audit Log Only]
    E -- "VERIFY/BLOCK" --> G[Fraud Case Created]
    G --> H[API Response]
```

## 3. Case Lifecycle
- **OPEN**: The default state when a suspicious transaction is flagged.
- **UNDER_REVIEW**: An analyst has acknowledged the case and is actively investigating.
- **RESOLVED**: The case is closed with a final resolution.
  - *CONFIRMED_FRAUD*: True positive.
  - *FALSE_POSITIVE*: Transaction was safe.
  - *VERIFIED_LEGITIMATE*: User passed Step-Up Authentication.

## 4. Database Architecture (SQLite)
The existing `transaction_audit_logs` table remains the immutable source of truth for every API request.
The new tables:
- **fraud_cases**: Tracks the current state of an investigation. Joins to `transaction_audit_logs` via `audit_log_id`.
- **case_history**: An append-only log tracking every status change, analyst assignment, and note added. Joins to `fraud_cases` via `case_id`.

## 5. Deduplication Strategy
If the exact same `transaction_id` is processed multiple times (e.g., due to client retries), the `CaseManager` queries the database before insertion. If a case for that `transaction_id` already exists, it skips creation and returns the existing `case_id`, preventing case spam.

## 6. API Architecture
- `POST /predict`: Evaluates transaction and optionally triggers case creation. Returns `case_id`.
- `GET /cases`: Lists cases (filterable by status/severity).
- `GET /cases/{id}`: Detailed view of a case and its history.
- `PATCH /cases/{id}/status`: Safe state machine transition endpoint for analysts.

## 7. Security Considerations
- The API currently uses a mocked `analyst_id`. In a real system, this requires OAuth2 / JWT injection.
- Case notes and historical transitions are immutable to prevent tampering by malicious insiders.

## 8. Prototype Limitations & Upgrades
- **SQLite Concurrency**: SQLite locks the whole DB on writes. Case creation adds write load. For production, PostgreSQL is required.
- **Async Processing**: Currently, case creation blocks the API response. In production, `CaseManager` should drop a message onto a Kafka or Pub/Sub queue, and a worker service should create the case asynchronously.
