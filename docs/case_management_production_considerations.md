# Case Management Production Considerations

While the current prototype effectively demonstrates a full fraud detection and case management lifecycle, deploying this system to an enterprise production environment (e.g., a Tier-1 Bank) requires several major architectural upgrades.

## 1. Database Infrastructure
- **Current**: SQLite (Local file-based).
- **Production**: PostgreSQL or Cloud Spanner. SQLite write-locks the entire file. At 100+ transactions per second (TPS), concurrent writes from the prediction API and analyst updates will cause severe latency spikes and timeouts.

## 2. Asynchronous Case Creation
- **Current**: Case creation happens synchronously within the `/predict` API request.
- **Production**: High-throughput systems must decouple prediction from alerting. The `/predict` endpoint should write to a high-speed log (e.g., Kafka, GCP Pub/Sub, AWS Kinesis). A separate background microservice should consume these events, evaluate the alert policy, and create cases.

## 3. Authentication & Authorization (IAM)
- **Current**: The API allows unauthenticated status transitions.
- **Production**: Requires OAuth2/OIDC. Endpoints must validate JWT tokens. Analysts must be assigned roles (e.g., `L1_ANALYST`, `FRAUD_MANAGER`) to restrict who can confirm fraud vs. just adding notes.

## 4. Notifications & PagerDuty Integration
- **Current**: Alerts live in the database and are viewed via Streamlit.
- **Production**: The Case Manager should integrate with PagerDuty, Slack, or email via webhooks for `CRITICAL` severity alerts, ensuring immediate human response.

## 5. Audit Immutability & Compliance
- **Current**: `case_history` is an append-only SQLite table, but the DB file itself can be edited by anyone with host access.
- **Production**: Compliance (e.g., PCI-DSS, SOC2) requires true immutability. Audit logs should be streamed to a WORM (Write Once Read Many) storage bucket or a secure ledger database (e.g., AWS QLDB).

## 6. Retention and Archiving
- **Current**: Indefinite retention in the main tables.
- **Production**: Cases older than 90 days should be offloaded to cold storage (e.g., AWS S3, BigQuery) to keep the operational relational database fast and lean.

## 7. Distributed Tracing & Idempotency
- **Current**: Simple `transaction_id` deduplication.
- **Production**: Requires robust Idempotency-Key headers and distributed tracing (OpenTelemetry) to track a transaction seamlessly from the Edge API Gateway through the ML models and into the Case system.
