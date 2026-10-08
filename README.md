# 🛡️ FRAUDSENSE AI
**Real-Time Pre-Authorization Fraud Detection System**

![Status](https://img.shields.io/badge/Status-Prototype-orange)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.103-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red)

FRAUDSENSE AI is an end-to-end engineering prototype for real-time, pre-authorization financial fraud detection. Built using the **PaySim** dataset, this project demonstrates a highly robust MLOps architecture that bridges the gap between raw machine learning probabilities and operational banking workflows.

See the [User Manual](USER_MANUAL.md) for setup, workflows, API usage, and troubleshooting.

---

## 🌟 Key Features

1. **Pre-Authorization Leakage Prevention** 🔒
   - Many academic fraud models accidentally train on "post-transaction" balances, creating artificially high accuracy. FRAUDSENSE AI utilizes strict **Pydantic API schemas** to air-gap and strip post-transaction variables before inference, ensuring a mathematically honest evaluation.
2. **Context-Aware Tri-State Decision Engine** ⚖️
   - Instead of simply outputting `Fraud (1)` or `Not Fraud (0)`, the system routes transactions into three operational states to reduce business friction (False Positives):
     - ✅ **APPROVE**: Low ML probability, low behavioral risk.
     - ⚠️ **VERIFY**: Medium risk. Routes to simulated step-up authentication (e.g., OTP/MFA).
     - 🚫 **BLOCK**: Extreme high probability.
3. **Behavioral Risk & Cold-Start Handling** 🧊
   - Real transaction datasets (like PaySim) are extremely sparse (99.85% of users transact only once). Our `BehavioralEngine` safely handles these cold-starts via explicit `NONE`, `LIMITED`, and `SUFFICIENT` states without crashing or hallucinating data.
4. **Fraud Analyst Dashboard** 📊
   - A fully functional **Streamlit** dashboard featuring live metrics, Case Management, and Model Drift tracking (Population Stability Index).

---

## 🏗️ System Architecture

1. **Transaction Entry**: A transaction hits the `FastAPI` endpoint.
2. **Validation**: The payload is validated. Leaking variables are dropped.
3. **Behavioral Engine**: Historical velocity is calculated (if history exists).
4. **Inference**: An `XGBoost` model calculates the baseline fraud probability.
5. **Decision Engine**: ML probability and behavioral risk are fused into an action (`APPROVE`/`VERIFY`/`BLOCK`).
6. **Case Management**: `VERIFY` and `BLOCK` transactions are written to a SQLite database for asynchronous analyst review.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- `pip`

### 1. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/YOUR_USERNAME/fraud-detection-ml.git
cd fraud-detection-ml
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Backend API
Start the FastAPI server:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
*The API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs)*

### 3. Run the Analyst Dashboard
In a new terminal window, start the Streamlit UI:
```bash
source venv/bin/activate
streamlit run app/streamlit_app.py --server.port=8501
```
*The dashboard will be available at [http://localhost:8501](http://localhost:8501)*

### 4. Run the React Operations Console

```bash
cd frontend
npm ci
npm run dev
```

The console is available at [http://localhost:5173](http://localhost:5173). Its dashboard is populated from persisted audit records rather than generated sample metrics.

## Production configuration

Copy [`.env.example`](.env.example), provide values through your platform’s secret manager, and set `ENVIRONMENT=production`. Production startup requires `API_KEY`; clients calling prediction, explanation, batch, and case-management endpoints must send it in `X-API-Key`. Configure explicit `CORS_ORIGINS`—wildcards are deliberately not accepted.

The deployed API also needs a compatible trained model and preprocessor at `MODEL_DIR` (default: `/app/models/pre_authorization`). Model artifacts are intentionally ignored by Git and must be supplied through the deployment pipeline or a protected model store.

Run local services with:

```bash
docker compose up --build
```

This exposes the API on `8000`, Streamlit on `8501`, and the React console on `5173`. Docker must be installed locally to use this workflow.

### Quality checks

```bash
pip install -r requirements-dev.txt
ruff check api database src tests
pytest -q
npm --prefix frontend run lint
npm --prefix frontend run build
```

---

## 🧪 Testing the API

Send a **Legitimate Transaction** (Expected output: `APPROVE`):
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/predict' \
  -H 'Content-Type: application/json' \
  -d '{
  "transaction_id": "DEMO_TXN_001",
  "channel": "NET_BANKING",
  "step": 1,
  "type": "PAYMENT",
  "amount": 100.0,
  "oldbalanceOrg": 5000.0,
  "oldbalanceDest": 0.0
}'
```

Send a **Fraudulent Transaction** (Expected output: `BLOCK` and a generated Case):
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/predict' \
  -H 'Content-Type: application/json' \
  -d '{
  "transaction_id": "DEMO_FRAUD_002",
  "channel": "UPI",
  "step": 1,
  "type": "TRANSFER",
  "amount": 2500000.0,
  "oldbalanceOrg": 2500000.0,
  "oldbalanceDest": 0.0
}'
```

---

## 📚 Project Structure

```text
├── api/                  # FastAPI routes, schemas, and services
├── app/                  # Streamlit dashboard application
├── config/               # YAML files for risk thresholds & drift bounds
├── database/             # SQLite models and connection setup
├── docs/                 # Extensive architectural and research documentation
├── models/               # Serialized ML models (XGBoost)
├── scripts/              # E2E simulation and load testing scripts
├── src/                  # Core logic (Decision Engine, Behavioral, Monitoring)
├── tests/                # Pytest unit and integration test suite
└── README.md
```

---

## ⚠️ Academic Limitations & Disclaimer

- **Dataset Constraints**: This prototype relies on the synthetic **PaySim** dataset. It does *not* natively represent the transaction topology of actual modern UPI, credit card, or net banking rails.
- **Prototype Database**: The system currently uses SQLite for local portability. For production deployment, this must be migrated to a concurrent database (e.g., PostgreSQL).
- **Security boundary**: API-key protection is available for stateful and model endpoints and mandatory in production. Deploy behind HTTPS and an identity-aware gateway for browser users; this repository does not implement end-user accounts or OAuth.

## 📄 License
This project is for academic and portfolio demonstration purposes.
