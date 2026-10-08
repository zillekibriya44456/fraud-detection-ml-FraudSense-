# FraudSense AI User Manual

## Start the application

Use two terminals from the repository root.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn api.main:app --reload --port 8000
```

The API health endpoint is <http://localhost:8000/health>; interactive API documentation is at <http://localhost:8000/docs>.

In a second terminal, start the React console:

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173>.

## Analyze a transaction

1. Select **Analyze Transaction** in the sidebar.
2. Enter a transaction ID, channel, type, step, amount, sender balance, and receiver balance.
3. Sender and receiver IDs are optional, but improve behavioral context.
4. Select **Analyze Transaction** and review the recommendation.

Recommendations mean:

- **APPROVE** — low detected risk.
- **VERIFY** — perform additional identity or payment verification.
- **BLOCK** — high risk; a case can be created automatically.

Only pre-transaction values are accepted. Do not include `newbalanceOrig` or `newbalanceDest`: these are post-transaction values and are rejected to prevent data leakage.

## Batch analysis

Open **Batch Analysis**, upload a CSV, then select **Start Analysis**. The required columns are:

```text
step,type,amount,oldbalanceOrg,oldbalanceDest
```

Optional columns are `transaction_id`, `channel`, `nameOrig`, and `nameDest`. Download the resulting CSV after processing.

## Scanners

- **Link Scanner** checks URL protocol, raw IP hosts, suspicious paths, and basic brand-impersonation signals. It does not visit the URL and cannot guarantee safety.
- **QR / UPI Scanner** parses UPI payloads such as `upi://pay?pa=merchant@upi&pn=Store&am=1500.00`.
- **Scam Analyzer** identifies common KYC, OTP, urgency, reward, and phishing wording in pasted messages.

Never disclose an OTP, PIN, or bank credentials based solely on scanner output.

## Dashboard, cases, and audit data

The Dashboard displays database-derived transaction audit totals, risk distribution, and the prior 24 hours of activity. An empty dashboard is normal until successful predictions are submitted.

Use **Case Management** to review elevated-risk cases. Valid status progression is `OPEN` → `UNDER_REVIEW` → `RESOLVED`; resolving a case requires a resolution value. Use **Audit Logs** for persisted prediction activity.

## API example

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"transaction_id":"TEST-001","channel":"UPI","step":1,"type":"TRANSFER","amount":20,"oldbalanceOrg":100,"oldbalanceDest":0}'
```

When `ENVIRONMENT=production`, include `-H 'X-API-Key: your-configured-api-key'` for protected model and case-management endpoints.

## Troubleshooting

| Problem | Resolution |
| --- | --- |
| `Model not loaded` | Supply compatible model files and `preprocessor.joblib` in `MODEL_DIR`. |
| API unreachable | Confirm Uvicorn runs on port 8000. |
| Console cannot connect | Confirm Vite runs on port 5173 and the API is running. |
| HTTP 422 | Check required fields, non-negative numeric values, and post-transaction fields. |
| HTTP 401 | Send the configured `X-API-Key` in production. |

## Verify installation

```bash
ruff check api database src tests
pytest -q
npm --prefix frontend run lint
npm --prefix frontend run build
```
