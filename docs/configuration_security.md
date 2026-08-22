# Configuration Security

## Current State
- The project utilizes a `.env` file (and `.env.example`) to manage configuration.
- The `docker-compose.yml` injects the `DB_URL` environment variable.

## Security Audit Findings
- **No Hardcoded Secrets**: We verified that `api/config.py` uses `os.getenv()` rather than hardcoding sensitive paths or keys.
- **`.env.example` Safety**: The example file contains only placeholders and safe defaults (e.g., `DB_URL=sqlite:///./data/audit_log.db`). It does not leak production credentials.

## Production Requirements (Future)
When migrating to a production environment (e.g., Kubernetes, Cloud Run), the following must be implemented:
1. **Secret Manager Integration**: API keys for external services, production Database URIs (e.g., PostgreSQL credentials), and JWT signing secrets must be injected at runtime via AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault.
2. **Environment Isolation**: The `debug=True` mode must strictly be disabled in production to prevent stack trace leakage. (Note: The current FastAPI global exception handler we introduced in Step 7 helps mitigate this).
3. **Immutability**: Configuration should be immutable per deployment. Any change to drift policy thresholds or risk parameters should require a formal code review and deployment, rather than hot-swapping files on a live server.
