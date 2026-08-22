# Logging & Observability

## Current State
The application uses Python's standard `logging` library. Currently, logs capture:
- Application startup and model loading.
- High-level endpoint access.
- Critical failures (e.g., "Critical Transaction Failure").

## Security Hardening
Logging in financial applications carries high compliance risks (e.g., PCI-DSS, GDPR).

### What MUST NOT be logged:
- **Personally Identifiable Information (PII)**: Full Names, unmasked account numbers.
- **Authentication Secrets**: Passwords, OTPs, Session Tokens, API Keys.
- **Sensitive Financial Data**: Full Credit Card numbers, CVV codes.

*Note: In the current prototype, the `nameOrig` and `nameDest` fields from PaySim are abstract IDs (e.g., `C12345`). In a real environment, these would be PII.*

### What MUST be logged:
- **Security Events**: Unauthorized access attempts, missing API keys.
- **Model Events**: Model loading failures, fallback triggers (`REVIEW_REQUIRED`).
- **Fraud Events**: System deciding to `BLOCK` or `VERIFY` a transaction.
- **Drift Events**: High PSI alerts from the Model Registry.

## Recommended Architecture (Future)
1. **Structured Logging**: Switch to JSON-formatted logs (e.g., using `structlog` or `jsonlogger`) to allow seamless ingestion into ELK (Elasticsearch, Logstash, Kibana), Datadog, or Splunk.
2. **Correlation IDs**: Inject a `X-Correlation-ID` into every incoming API request and propagate it through the ML pipeline, database, and logs. This is essential for tracing a transaction's lifecycle across microservices.
