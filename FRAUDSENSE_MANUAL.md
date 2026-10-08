# FraudSense AI — Complete Command & Operations Manual
> Version: 1.0.0 | Last Updated: Oct 2026
> Every command verified against actual project source code.

---

## Table of Contents
1. Project Overview
2. Technology Stack
3. Architecture
4. Folder Structure
5. Environment Setup
6. Dependency Setup
7. Environment Variables
8. Dataset Pipeline
9. ML Training
10. Model Management
11. Backend
12. API Reference
13. Frontend
14. Database
15. Docker
16. Testing
17. Debugging Manual
18. Git
19. Deployment
20. Production Readiness Audit
21. Antigravity to Manual Mapping
22. Start From Zero
23. Emergency Recovery
24. Master Cheat Sheet — 20 Most Important Commands

---

## 1. Project Overview

FraudSense AI is an Autonomous Financial Intelligence & Fraud Prevention platform. It accepts financial
transaction data from 8 distinct domains and predicts fraud probability in real time using a multi-domain
XGBoost ML engine.

Domains Supported:
| Domain       | Description                           | Dataset File                                    |
|--------------|---------------------------------------|-------------------------------------------------|
| paysim       | Mobile Money / PaySim simulation      | PS_20174392719_1491204439457_log.csv            |
| bank         | Credit applications / Bank fraud      | Bank transactions/ dir                          |
| upi          | UPI payment transactions              | upi_transactions_2024.csv                       |
| card         | Credit card fraud (PCA-anonymized)    | creditcard.csv                                  |
| bitcoin      | Bitcoin/Elliptic blockchain fraud     | elliptic_bitcoin_dataset/ dir                   |
| url_phishing | Phishing URL detection                | PhiUSIIL_Phishing_URL_Dataset.csv               |
| sms          | SMS scam / spam detection             | (SMS)sms+spam+collection/ dir                   |
| email        | Email phishing detection              | Email 2/ dir                                    |

---

## 2. Technology Stack

| Layer              | Technology                        | Version                     |
|--------------------|-----------------------------------|-----------------------------|
| Backend API        | FastAPI + Uvicorn                 | >=0.110,<1 / >=0.27,<1      |
| Frontend           | React + TypeScript + Vite         | React ^19.2.8, Vite ^8.3.0  |
| UI Charts          | Recharts                          | ^3.10.1                     |
| UI Icons           | Lucide-React                      | ^1.52.0                     |
| UI Animations      | Framer-Motion                     | ^14.0.0                     |
| Alternative UI     | Streamlit                         | >=1.32,<2                   |
| ML Models          | XGBoost                           | >=2,<4                      |
| ML Preprocessing   | Scikit-Learn                      | >=1.4,<2                    |
| Imbalance Handling | Imbalanced-Learn (SMOTE)          | >=0.12,<1                   |
| Explainability     | SHAP                              | >=0.45,<1                   |
| Data               | Pandas + NumPy                    | >=2.2,<3 / >=1.26,<3        |
| Database           | SQLite (dev) via SQLAlchemy       | >=2,<3                      |
| Auth               | JWT + API Key                     | Built-in api/security.py    |
| Containerization   | Docker + Docker Compose + Nginx   | Latest                      |
| Testing            | Pytest                            | >=8,<9                      |
| Linting            | Ruff (backend) + Oxlint (frontend)|                             |

---

## 3. Architecture

    React/Vite Frontend (Port 5173 dev / Port 80 Docker Nginx)
                           |
                    /api/* proxy
                           |
    FastAPI Backend (Port 8000)
      api/main.py, api/routes.py, api/case_routes.py
      api/monitoring_routes.py, api/intelligence_routes.py
                           |
         +-----------------+------------------+
         |                                    |
    DomainRiskEngine                    SQLite Database
    src/risk_engine.py                  data/audit_log.db
    Routes by `domain` key              TransactionAuditLog
                                        FraudCase / CaseHistory
         |
    models/ directory
    paysim/ bank/ upi/ card/ bitcoin/ sms/ email/ url_phishing/ pre_authorization/

---

## 4. Folder Structure

    fraud-detection-ml/
    ├── api/
    │   ├── main.py                 # App entry, middleware, exception handlers
    │   ├── routes.py               # /predict, /predict_batch, /explain, /dashboard/summary
    │   ├── case_routes.py          # /cases/* endpoints
    │   ├── monitoring_routes.py    # /monitoring/* endpoints
    │   ├── intelligence_routes.py  # /api/v1/* (URL, QR, SMS, Copilot)
    │   ├── schemas.py              # Pydantic models
    │   ├── security.py             # JWT + API Key auth + rate limiter
    │   └── services.py             # FraudService wrapper
    ├── src/
    │   ├── risk_engine.py          # DomainRiskEngine multi-domain ML router
    │   ├── train_paysim.py         # PaySim training script
    │   ├── train_bank.py           # Bank fraud training
    │   ├── train_upi.py            # UPI fraud training
    │   ├── train_card.py           # Credit card training
    │   ├── train_bitcoin.py        # Bitcoin fraud training
    │   ├── train_url_phishing.py   # URL phishing training
    │   ├── train_sms.py            # SMS scam training
    │   ├── train_email.py          # Email phishing training
    │   ├── decision_engine.py      # Risk policy decision logic
    │   ├── explainability.py       # SHAP explainability wrapper
    │   ├── case_manager.py         # Automatic fraud case creation
    │   ├── monitoring/             # Drift & performance analysis
    │   └── settings.py             # Settings loaded from env vars
    ├── models/
    │   ├── pre_authorization/      # Legacy PaySim model (JSON + joblib)
    │   ├── paysim/                 # model.joblib + preprocessor.joblib
    │   ├── bank/ upi/ card/ bitcoin/ sms/ email/ url_phishing/
    │   └── model_registry.json     # Master model registry
    ├── dataset/                    # Raw datasets (excluded from Docker)
    │   ├── PS_20174392719_1491204439457_log.csv  (493MB)
    │   ├── creditcard.csv                         (151MB)
    │   ├── upi_transactions_2024.csv              (30MB)
    │   ├── PhiUSIIL_Phishing_URL_Dataset.csv     (57MB)
    │   ├── (SMS)sms+spam+collection/
    │   ├── elliptic_bitcoin_dataset/
    │   ├── Bank transactions/
    │   └── Email 2/
    ├── frontend/
    │   ├── src/                    # TypeScript source
    │   ├── package.json            # npm scripts: dev, build, lint, preview
    │   ├── vite.config.ts          # Vite + API proxy config
    │   └── nginx.conf              # Production Nginx reverse proxy
    ├── database/                   # SQLAlchemy models + DB connection
    ├── scripts/
    │   ├── simulate_traffic.py     # Multi-domain API load tester
    │   ├── e2e_simulation.py       # End-to-end simulation
    │   ├── verify.py               # System verification
    │   └── performance_test.py     # Performance benchmarking
    ├── tests/                      # Pytest test suite
    │   ├── test_api.py
    │   ├── test_upi_model.py, test_card_model.py, test_sms_model.py
    │   ├── test_url_model.py, test_decision_engine.py
    │   ├── test_behavioral.py, test_case_management.py, test_monitoring.py
    ├── .env                        # Active env vars (DO NOT COMMIT)
    ├── .env.example                # Template
    ├── .dockerignore               # Excludes dataset/, venv/, dist/
    ├── docker-compose.yml          # Multi-service Docker setup
    ├── Dockerfile.api              # Python 3.11-slim API image
    ├── Dockerfile.frontend         # Node 22 → Nginx React image
    ├── Dockerfile.ui               # Streamlit UI image
    ├── requirements.txt            # Python production dependencies
    ├── requirements-dev.txt        # Dev deps (adds ruff)
    └── deploy.sh                   # One-command deployment script

---

## 5. Environment Setup

### Check Prerequisites

    # Python 3.11+
    python3 --version

    # Node.js 22+
    node --version

    # Docker
    docker --version
    docker-compose --version

### Create Python Virtual Environment

SOURCE: Standard Python venv

    python3 -m venv venv
    source venv/bin/activate
    which python   # Should show .../fraud-detection-ml/venv/bin/python

---

## 6. Dependency Setup

### Backend

SOURCE: requirements.txt

    venv/bin/pip install -r requirements.txt

    # For development (adds ruff linter)
    # SOURCE: requirements-dev.txt
    venv/bin/pip install -r requirements-dev.txt

### Frontend

SOURCE: frontend/package.json

    cd frontend
    npm install

---

## 7. Environment Variables

Variables are loaded by src/settings.py from .env.

| Variable     | Purpose                        | Default                         | Required in Prod |
|--------------|--------------------------------|---------------------------------|-----------------|
| ENVIRONMENT  | development or production      | development                     | YES             |
| API_KEY      | API authentication secret      | None                            | YES (required)  |
| JWT_SECRET   | JWT signing secret             | falls back to api_key           | Recommended     |
| DATABASE_URL | SQLAlchemy connection string   | sqlite:///./data/audit_log.db   | Use PostgreSQL  |
| MODEL_DIR    | Pre-auth model directory path  | models/pre_authorization        | No              |
| CORS_ORIGINS | Allowed browser origins        | http://localhost:5173,...        | YES             |

### Configure

    cp .env.example .env
    nano .env

    # Minimum production .env:
    # ENVIRONMENT=production
    # API_KEY=your_super_secret_random_key_here
    # JWT_SECRET=another_long_random_secret
    # DATABASE_URL=sqlite:///./data/audit_log.db
    # MODEL_DIR=/app/models/pre_authorization
    # CORS_ORIGINS=http://localhost:5173,http://localhost:80

---

## 8. Dataset Pipeline

IMPORTANT: Datasets are in dataset/. They are excluded from Docker builds via .dockerignore.

### Actual Datasets

| Domain       | File                                     | Size  | Format    | Target Column |
|--------------|------------------------------------------|-------|-----------|---------------|
| PaySim       | PS_20174392719_1491204439457_log.csv     | 493MB | CSV       | isFraud       |
| Credit Card  | creditcard.csv                           | 151MB | CSV (PCA) | Class         |
| UPI          | upi_transactions_2024.csv                | 30MB  | CSV       | Is Fraud      |
| URL Phishing | PhiUSIIL_Phishing_URL_Dataset.csv        | 57MB  | CSV       | label         |
| SMS          | (SMS)sms+spam+collection/ dir            | dir   | text      | spam/ham      |
| Bitcoin      | elliptic_bitcoin_dataset/ dir            | dir   | CSV graph | class         |
| Bank         | Bank transactions/ dir                   | dir   | CSV       | fraud_bool    |
| Email        | Email 2/ dir                             | dir   | text      | phishing      |

### Dataset Verification Commands

SOURCE: scripts/phase2_verify_datasets.py

    venv/bin/python -m scripts.phase2_verify_datasets

SOURCE: scripts/phase3_dataset_understanding.py

    venv/bin/python -m scripts.phase3_dataset_understanding

SOURCE: scripts/phase4_exploratory_data_analysis.py

    venv/bin/python -m scripts.phase4_exploratory_data_analysis

---

## 9. ML Training

### Pipeline (Same for All Domains)

    Raw CSV/text
      -> pandas read_csv()
      -> Preprocessing (ColumnTransformer: SimpleImputer + StandardScaler + OneHotEncoder)
      -> IsolationForest anomaly score augmentation (n_estimators=100, contamination=0.002)
      -> SMOTE oversampling (sampling_strategy=0.05, k_neighbors=3)
      -> XGBoost training (scale_pos_weight for class imbalance)
      -> F2-optimal threshold calibration
      -> Save model.joblib + preprocessor.joblib + metrics.json -> models/<domain>/

### Training Commands (Per Domain)

    # PaySim / Mobile Money
    # SOURCE: src/train_paysim.py
    # Dataset: dataset/PS_20174392719_1491204439457_log.csv
    # Output: models/paysim/model.joblib + models/pre_authorization/xgboost_fraud_model.json
    venv/bin/python -m src.train_paysim

    # Bank Fraud
    # SOURCE: src/train_bank.py
    # Dataset: dataset/Bank transactions/
    # Output: models/bank/model.joblib
    venv/bin/python -m src.train_bank

    # UPI Fraud
    # SOURCE: src/train_upi.py
    # Dataset: dataset/upi_transactions_2024.csv
    # Output: models/upi/model.joblib
    venv/bin/python -m src.train_upi

    # Credit Card Fraud
    # SOURCE: src/train_card.py
    # Dataset: dataset/creditcard.csv
    # Output: models/card/model.joblib
    venv/bin/python -m src.train_card

    # Bitcoin Fraud
    # SOURCE: src/train_bitcoin.py
    # Dataset: dataset/elliptic_bitcoin_dataset/
    # Output: models/bitcoin/model.joblib
    venv/bin/python -m src.train_bitcoin

    # URL Phishing
    # SOURCE: src/train_url_phishing.py
    # Dataset: dataset/PhiUSIIL_Phishing_URL_Dataset.csv
    # Output: models/url_phishing/model.joblib
    venv/bin/python -m src.train_url_phishing

    # SMS Spam / Scam
    # SOURCE: src/train_sms.py
    # Dataset: dataset/(SMS)sms+spam+collection/
    # Output: models/sms/model.joblib
    venv/bin/python -m src.train_sms

    # Email Phishing
    # SOURCE: src/train_email.py
    # Dataset: dataset/Email 2/
    # Output: models/email/model.joblib
    venv/bin/python -m src.train_email

    # Train ALL models sequentially (requires all datasets)
    venv/bin/python -m src.train_paysim && \
    venv/bin/python -m src.train_bank && \
    venv/bin/python -m src.train_upi && \
    venv/bin/python -m src.train_card && \
    venv/bin/python -m src.train_bitcoin && \
    venv/bin/python -m src.train_url_phishing && \
    venv/bin/python -m src.train_sms && \
    venv/bin/python -m src.train_email

### Model Evaluation

SOURCE: src/evaluate.py

    venv/bin/python -m src.evaluate

SOURCE: evaluate_decision_engine.py (root-level)

    venv/bin/python evaluate_decision_engine.py

---

## 10. Model Management

### View Model Registry

SOURCE: models/model_registry.json

    cat models/model_registry.json

### Domain to Model File Mapping

| Domain       | Model File                                          | Preprocessor                                       |
|--------------|-----------------------------------------------------|----------------------------------------------------|
| paysim       | models/paysim/model.joblib                          | models/paysim/preprocessor.joblib                  |
| mobile_money | models/pre_authorization/xgboost_fraud_model.json   | models/pre_authorization/preprocessor.joblib        |
| bank         | models/bank/model.joblib                            | models/bank/preprocessor.joblib                    |
| upi          | models/upi/model.joblib                             | models/upi/preprocessor.joblib                     |
| card         | models/card/model.joblib                            | models/card/preprocessor.joblib                    |
| bitcoin      | models/bitcoin/model.joblib                         | models/bitcoin/preprocessor.joblib                 |
| url_phishing | models/url_phishing/model.joblib                    | models/url_phishing/preprocessor.joblib             |
| sms          | models/sms/model.joblib                             | models/sms/preprocessor.joblib                     |
| email        | models/email/model.joblib                           | models/email/preprocessor.joblib                   |

### Manually Verify a Model Loads

    # Verify UPI model
    venv/bin/python -c "
    import joblib
    m = joblib.load('models/upi/model.joblib')
    p = joblib.load('models/upi/preprocessor.joblib')
    print('UPI model loaded OK:', type(m))
    "

    # Verify pre_authorization (PaySim) model
    venv/bin/python -c "
    import xgboost as xgb, joblib
    model = xgb.XGBClassifier()
    model.load_model('models/pre_authorization/xgboost_fraud_model.json')
    prep = joblib.load('models/pre_authorization/preprocessor.joblib')
    print('Pre-auth model OK. Features:', model.n_features_in_)
    "

    # List all model files
    ls models/paysim/ models/bank/ models/upi/ models/card/ models/bitcoin/ models/sms/ models/email/ models/url_phishing/

---

## 11. Backend

### Development Start (with auto-reload)

SOURCE: Dockerfile.api CMD directive

    venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

### Production Start (no reload)

    venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

### Health Checks

    # Basic liveness
    curl http://localhost:8000/health
    # Expected: {"status":"healthy","environment":"development"}

    # Readiness (model loaded?)
    curl http://localhost:8000/readiness
    # Expected: {"status":"ready","model_loaded":true}

    # API root
    curl http://localhost:8000/
    # Expected: {"service":"FraudSense AI","environment":"development"}

### API Swagger Docs (browser)

    open http://localhost:8000/docs

    # OpenAPI JSON
    curl http://localhost:8000/openapi.json

---

## 12. API Reference

All endpoints verified from api/routes.py, api/case_routes.py, api/monitoring_routes.py,
api/intelligence_routes.py.

### POST /predict
Purpose: Predict fraud for a single transaction (any domain)
Auth: Optional X-API-Key header (required in production)
Source: api/routes.py

    # PAYSIM — suspicious large transfer
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"paysim","transaction_id":"TX_001","step":1,"type":"TRANSFER","amount":150000.0,"oldbalanceOrg":150000.0,"oldbalanceDest":0.0}'

    # BANK
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"bank","transaction_id":"TX_002","income":0.5,"name_email_similarity":0.8,"velocity_6h":100,"velocity_24h":200,"velocity_4w":300,"bank_branch_count_8w":5,"date_of_birth_distinct_emails_4w":1,"credit_risk_score":150,"email_is_free":1,"phone_home_valid":1,"phone_mobile_valid":1,"bank_months_count":12,"has_other_cards":0,"proposed_credit_limit":1000,"foreign_request":0,"session_length_in_minutes":5,"keep_alive_session":1,"device_os":0,"device_distinct_emails_8w":1,"month":5}'

    # UPI
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"upi","transaction_id":"TX_003","amount":15000.0,"transaction_type":"P2P","merchant_category":"Shopping","sender_bank":"HDFC","receiver_bank":"SBI","hour_of_day":14,"day_of_week":"Monday","sender_age_group":"26-35","receiver_age_group":"26-35"}'

    # CARD
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"card","transaction_id":"TX_004","Amount":125.50,"Time":3600,"V1":-1.3,"V2":0.5,"V3":1.2,"V4":0.1,"V5":-0.8}'

    # BITCOIN
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"bitcoin","transaction_id":"TX_005","time_step":20}'

    # URL PHISHING
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"url_phishing","transaction_id":"TX_006","url":"http://secure-login-chase-update.example/login"}'

    # SMS
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"sms","transaction_id":"TX_007","text":"URGENT: Your account is blocked. Verify KYC at http://evil-bank.com"}'

    # EMAIL
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"email","transaction_id":"TX_008","text":"Your bank account is suspended. Verify credentials immediately."}'

Expected Response (200 OK):
    {
      "prediction": "Fraud",
      "fraud_probability": 0.94,
      "risk_level": "HIGH",
      "recommended_action": "BLOCK",
      "decision_policy": "R1_HIGH_RISK_BLOCK",
      "decision_confidence": "HIGH_CONFIDENCE",
      "policy_version": "v2.0",
      "decision_reasons": ["..."],
      "model_version": "upi_fraud_detector",
      "inference_latency_ms": 12.4,
      "audit_id": 7,
      "case_id": "CASE_XXXXX",
      "feature_schema_version": "v2.0_multi_domain",
      "realtime_feature_validation": "passed",
      "behavioral_history_status": "NONE",
      "behavioral_risk_signal": 0.0
    }

### POST /predict_batch
Purpose: Predict fraud for multiple transactions at once
Source: api/routes.py

    curl -X POST http://localhost:8000/predict_batch \
      -H "Content-Type: application/json" \
      -d '{"transactions":[{"domain":"sms","text":"Your OTP is 123456"},{"domain":"paysim","step":1,"type":"TRANSFER","amount":200000.0,"oldbalanceOrg":200000.0,"oldbalanceDest":0.0}]}'

### POST /explain
Purpose: Get SHAP feature importance for a prediction
Source: api/routes.py

    curl -X POST http://localhost:8000/explain \
      -H "Content-Type: application/json" \
      -d '{"domain":"paysim","step":1,"type":"TRANSFER","amount":150000.0,"oldbalanceOrg":150000.0,"oldbalanceDest":0.0}'

### GET /dashboard/summary
Purpose: Aggregate stats from audit log DB
Source: api/routes.py

    curl http://localhost:8000/dashboard/summary

### Case Management Endpoints (api/case_routes.py)

    # List all cases
    curl http://localhost:8000/cases/

    # Filter by status/severity
    curl "http://localhost:8000/cases/?status=OPEN&severity=HIGH"

    # Get specific case
    curl http://localhost:8000/cases/CASE_AF0E3596

    # Update case status
    curl -X PATCH http://localhost:8000/cases/CASE_AF0E3596/status \
      -H "Content-Type: application/json" \
      -d '{"status":"RESOLVED","resolution":"CONFIRMED_FRAUD","notes":"Verified by analyst.","analyst_id":"analyst_01"}'

### Monitoring Endpoints (api/monitoring_routes.py)

    curl http://localhost:8000/monitoring/drift
    curl http://localhost:8000/monitoring/performance
    curl http://localhost:8000/monitoring/registry
    curl http://localhost:8000/monitoring/retraining-recommendation

### Intelligence Endpoints (api/intelligence_routes.py)

    # URL phishing scanner
    curl -X POST http://localhost:8000/api/v1/scans/url \
      -H "Content-Type: application/json" \
      -d '{"url":"http://secure-login-chase-update.example/login"}'

    # UPI QR scanner
    curl -X POST http://localhost:8000/api/v1/scans/qr \
      -H "Content-Type: application/json" \
      -d '{"payload":"upi://pay?pa=merchant@upi&pn=Store&am=500.00"}'

    # SMS scam analyzer
    curl -X POST http://localhost:8000/api/v1/scans/sms \
      -H "Content-Type: application/json" \
      -d '{"text":"URGENT: Your account is blocked. Verify KYC at http://evil-bank.com"}'

    # Email scam analyzer (same endpoint as SMS)
    curl -X POST http://localhost:8000/api/v1/scans/email \
      -H "Content-Type: application/json" \
      -d '{"text":"Your bank account is suspended. Verify credentials immediately."}'

    # AI Copilot chat
    curl -X POST http://localhost:8000/api/v1/copilot/chat \
      -H "Content-Type: application/json" \
      -d '{"message":"Is this safe? http://secure-login-chase-update.example/login"}'

    # Dedicated UPI predict endpoint
    curl -X POST http://localhost:8000/api/v1/predict/upi \
      -H "Content-Type: application/json" \
      -d '{"amount":50000,"transaction_type":"P2M","hour_of_day":2}'

    # Threat intelligence feed
    curl http://localhost:8000/api/v1/threat-intelligence

    # Audit logs (last 50)
    curl http://localhost:8000/api/v1/audit/logs

---

## 13. Frontend

### Development Server

SOURCE: frontend/package.json scripts.dev = "vite"

    cd frontend
    npm run dev
    # Access: http://localhost:5173

### Production Build

SOURCE: frontend/package.json scripts.build = "tsc -b && vite build"

    cd frontend
    npm run build
    # Output: frontend/dist/

### Preview Production Build Locally

SOURCE: frontend/package.json scripts.preview = "vite preview"

    cd frontend
    npm run preview

### Lint

SOURCE: frontend/package.json scripts.lint = "oxlint"

    cd frontend
    npm run lint

### How Frontend Connects to Backend
- Development: Vite dev server proxies /api/* requests to http://localhost:8000 via frontend/vite.config.ts
- Production (Docker): Nginx (frontend/nginx.conf) proxies:
  - /api/v1/* -> http://api:8000/api/v1/
  - /api/*    -> http://api:8000/

---

## 14. Database

Technology: SQLite (development) via SQLAlchemy 2.x
File: data/audit_log.db

Tables:
| Table                 | Description                                        |
|-----------------------|----------------------------------------------------|
| transaction_audit_log | Every prediction recorded automatically            |
| fraud_case            | Auto-created when fraud probability > threshold    |
| case_history          | Full audit trail of case status changes            |

### Commands

    # View last 10 audit log entries
    venv/bin/python -c "
    from database.database import SessionLocal
    from database.models import TransactionAuditLog
    db = SessionLocal()
    logs = db.query(TransactionAuditLog).order_by(TransactionAuditLog.id.desc()).limit(10).all()
    for l in logs:
        print(l.id, l.prediction, l.fraud_probability, l.risk_level)
    db.close()
    "

    # View fraud cases
    venv/bin/python -c "
    from database.database import SessionLocal
    from database.models import FraudCase
    db = SessionLocal()
    cases = db.query(FraudCase).limit(10).all()
    for c in cases:
        print(c.id, c.status, c.severity)
    db.close()
    "

    # Reset the database (DANGER: deletes all audit data)
    rm -f data/audit_log.db
    # DB is recreated automatically on next backend start

---

## 15. Docker

### Deployment (Recommended)

SOURCE: deploy.sh

    ./deploy.sh
    # Expected: 8/8 containers healthy, exit code 0

### Manual Docker Compose Commands

    # Build all images
    docker-compose build

    # Build specific service
    docker-compose build api
    docker-compose build frontend
    docker-compose build ui

    # Force full rebuild (no cache)
    docker-compose build --no-cache

    # Start all services in background
    docker-compose up -d

    # Start and stream logs to terminal
    docker-compose up

    # Stop all services
    docker-compose down

    # Stop and remove volumes (resets database)
    docker-compose down -v

    # Restart a specific service
    docker-compose restart api

    # Rebuild and restart
    docker-compose up -d --build

    # View logs (all services)
    docker-compose logs -f

    # View logs (backend only)
    docker-compose logs -f api

    # View logs (frontend/Nginx)
    docker-compose logs -f frontend

    # View logs (Streamlit UI)
    docker-compose logs -f ui

    # List running containers
    docker-compose ps
    docker ps

    # Shell into a running container
    docker exec -it fraud-detection-ml-api-1 bash
    docker exec -it fraud-detection-ml-frontend-1 sh

    # Check container health status
    docker inspect --format='{{.State.Health.Status}}' fraud-detection-ml-api-1

    # Free up Docker disk space (fixes Read-Only FS errors)
    docker system prune -f

    # Deep clean including all volumes and images (CAUTION)
    docker system prune -a --volumes -f

### Services Exposed

| Service            | Container                       | Host Port | Internal Port |
|--------------------|---------------------------------|-----------|---------------|
| API (FastAPI)      | fraud-detection-ml-api-1        | 8000      | 8000          |
| Frontend (Nginx)   | fraud-detection-ml-frontend-1   | 5173      | 80            |
| Streamlit UI       | fraud-detection-ml-ui-1         | 8501      | 8501          |

---

## 16. Testing

### Pytest — Unit & Integration Tests

    # Run entire test suite
    # SOURCE: tests/ directory
    venv/bin/pytest tests/

    # Verbose output
    venv/bin/pytest tests/ -v

    # Specific test files
    venv/bin/pytest tests/test_api.py -v
    venv/bin/pytest tests/test_upi_model.py -v
    venv/bin/pytest tests/test_card_model.py -v
    venv/bin/pytest tests/test_sms_model.py -v
    venv/bin/pytest tests/test_url_model.py -v
    venv/bin/pytest tests/test_decision_engine.py -v
    venv/bin/pytest tests/test_case_management.py -v
    venv/bin/pytest tests/test_monitoring.py -v
    venv/bin/pytest tests/test_behavioral.py -v

    # Specific test function
    venv/bin/pytest tests/test_api.py::test_health_check -v

    # Show print output
    venv/bin/pytest tests/ -s

### API Traffic Simulation

SOURCE: scripts/simulate_traffic.py
NOTE: Hits http://localhost:8000/api/v1/predict (multi-threaded, all 6 domains)

    venv/bin/python -m scripts.simulate_traffic
    # Stop with Ctrl+C

### Performance Testing

SOURCE: scripts/performance_test.py

    venv/bin/python -m scripts.performance_test

### End-to-End Simulation

SOURCE: scripts/e2e_simulation.py

    venv/bin/python -m scripts.e2e_simulation

### System Verification

SOURCE: scripts/verify.py

    venv/bin/python -m scripts.verify

### Manual API Tests

    # Legitimate transaction (should APPROVE)
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"paysim","step":1,"type":"PAYMENT","amount":200.0,"oldbalanceOrg":5000.0,"oldbalanceDest":1000.0}'
    # Expected: risk_level=LOW, recommended_action=APPROVE

    # Suspicious transaction (should BLOCK)
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"paysim","step":1,"type":"TRANSFER","amount":150000.0,"oldbalanceOrg":150000.0,"oldbalanceDest":0.0}'
    # Expected: risk_level=HIGH or CRITICAL, recommended_action=BLOCK

    # Invalid payload — post-auth leakage (should 422)
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"paysim","step":1,"type":"TRANSFER","amount":100.0,"oldbalanceOrg":100.0,"oldbalanceDest":0.0,"newbalanceOrig":0.0,"newbalanceDest":100.0}'
    # Expected: HTTP 422 Unprocessable Entity

---

## 17. Debugging Manual

### Backend Not Starting — ImportError / ModuleNotFoundError

    SYMPTOM: ModuleNotFoundError: No module named 'fastapi'
    CHECK:   which python   # Must show venv/bin/python
    CAUSE:   venv not activated
    FIX:     source venv/bin/activate
             pip install -r requirements.txt

### Backend Not Starting — API_KEY Error

    SYMPTOM: RuntimeError: API_KEY must be configured when ENVIRONMENT=production
    CAUSE:   .env has ENVIRONMENT=production but no API_KEY set
    FIX:     echo "API_KEY=my_secure_key" >> .env

### Port Already in Use

    SYMPTOM: OSError: [Errno 48] Address already in use (port 8000)
    CHECK:   lsof -i :8000
    FIX:     kill -9 $(lsof -ti :8000)

    # For frontend port 5173
    kill -9 $(lsof -ti :5173)

### Frontend Not Starting — npm Not Found

    SYMPTOM: npm: command not found
    FIX:     brew install node@22

### Frontend Missing Dependencies

    SYMPTOM: Cannot find module 'react'
    FIX:     cd frontend
             rm -rf node_modules package-lock.json
             npm install

### API 422 Errors

    SYMPTOM: {"detail":[{"type":"missing","loc":["body","step"],"msg":"Field required"},...]}
    CAUSE 1: Payload contains newbalanceOrig or newbalanceDest (forbidden by leakage guard)
    CAUSE 2: "domain" key is missing from payload
    FIX:     Ensure payload has "domain" key.
             Never include newbalanceOrig or newbalanceDest in any payload.

### Model Not Loading (503 Service Unavailable)

    SYMPTOM: {"detail":"Model not loaded."}
    CHECK:   ls models/pre_authorization/   # Must have xgboost_fraud_model.json
             ls models/upi/                 # Must have model.joblib
    CAUSE:   Model files missing (not trained yet)
    FIX:     venv/bin/python -m src.train_upi
             venv/bin/python -m src.train_paysim

### Docker Build — Read-Only File System

    SYMPTOM: [Errno 30] Read-only file system
             write .../dataset/...: read-only file system
    CAUSE:   Docker virtual disk is full (dataset/ was copied into image)
    CHECK:   cat .dockerignore | grep dataset
    FIX 1:   echo "dataset/" >> .dockerignore
    FIX 2:   docker system prune -f
    THEN:    ./deploy.sh

### Docker Daemon Not Running

    SYMPTOM: Cannot connect to the Docker daemon at unix:///Users/...docker.sock
    FIX:     open -a Docker
             # Wait ~30 seconds, then retry:
             ./deploy.sh

### CORS Error in Browser

    SYMPTOM: Access to fetch at '...' from origin '...' has been blocked by CORS policy
    CAUSE:   Frontend URL not in CORS_ORIGINS
    FIX:     Add your URL to CORS_ORIGINS in .env, e.g.:
             CORS_ORIGINS=https://yourfrontend.com,http://localhost:5173
             Then restart backend.

### Scikit-Learn Version Warning

    SYMPTOM: InconsistentVersionWarning: Trying to unpickle estimator from version 1.9.0 when using 1.6.1
    CAUSE:   Model was trained with a different sklearn version than what is installed in venv
    FIX:     Retrain the model with the current installed sklearn version:
             venv/bin/python -m src.train_upi

---

## 18. Git

    # Check status
    git status

    # Add all changes
    git add .

    # Commit
    git commit -m "feat: add UPI model training"

    # Push to remote
    git push origin main

    # Create new branch
    git checkout -b feature/my-feature

    # Pull latest
    git pull origin main

    # View log
    git log --oneline -20

    # IMPORTANT: Never commit .env (already in .gitignore)
    # IMPORTANT: Never commit dataset/ or models/ (too large for git)

---

## 19. Deployment

### One-Command Deployment

SOURCE: deploy.sh — requires Docker Desktop running + .env configured

    ./deploy.sh

### What deploy.sh Does
1. Checks if .env exists (exits with instructions if not found)
2. Runs: docker-compose up -d --build
3. Prints URLs of each running service

### Deployment Checklist (Before Going Public)
- [ ] ENVIRONMENT=production set in .env
- [ ] API_KEY set to a long random secret (min 32 chars)
- [ ] JWT_SECRET set separately
- [ ] CORS_ORIGINS set to your actual public domain (not localhost)
- [ ] All 8 domain models trained and present in models/
- [ ] dataset/ in .dockerignore (prevents OOM during build)
- [ ] Docker Desktop running
- [ ] Ports 8000, 5173, 8501 open on server firewall
- [ ] HTTPS via Nginx reverse proxy (for public deployment)

---

## 20. Production Readiness Audit

| Area                  | Status              | Evidence                                           | Action Needed                   |
|-----------------------|---------------------|----------------------------------------------------|---------------------------------|
| API Key Auth          | READY               | api/security.py enforces API key in production     | Set API_KEY in .env             |
| JWT Support           | READY               | Dual JWT + API Key auth in api/security.py         | Install PyJWT if using JWT      |
| CORS                  | READY               | Configurable via CORS_ORIGINS env var              | Set to real domain              |
| Input Validation      | READY               | Pydantic v2 with model_validator leakage guard     | —                               |
| Rate Limiting         | NEEDS IMPROVEMENT   | In-memory sliding window (60 req/min per key)      | Use Redis for multi-node        |
| Error Handling        | READY               | Global exception handlers in api/main.py           | —                               |
| Security Headers      | READY               | X-Frame-Options, X-Content-Type-Options, etc.      | —                               |
| Logging               | READY               | Structured per-request logging in middleware       | Add log aggregation (Loki/ELK)  |
| Database              | NEEDS IMPROVEMENT   | SQLite single-file (not suitable for high traffic) | Migrate to PostgreSQL           |
| HTTPS                 | NEEDS IMPROVEMENT   | Not in Docker Compose                              | Add Nginx + Let's Encrypt       |
| Model Versioning      | READY               | models/model_registry.json tracks all versions     | —                               |
| Model Drift           | READY               | src/monitoring/drift_analyzer.py + API endpoint    | —                               |
| SHAP Explainability   | READY               | /explain endpoint + src/explainability.py          | —                               |
| Class Imbalance       | READY               | SMOTE + scale_pos_weight in all train scripts      | —                               |
| Docker Security       | READY               | Non-root appuser (uid 10001) in Dockerfile.api     | —                               |
| Secrets in VCS        | READY               | .env is in .gitignore                              | Never commit .env               |
| Dataset in Docker     | READY               | dataset/ and *.zip in .dockerignore                | —                               |

---

## 21. Antigravity to Manual Operation Mapping

| ANTIGRAVITY OPERATION    | MANUAL COMMAND                                                                | SOURCE FILE              |
|--------------------------|-------------------------------------------------------------------------------|--------------------------|
| Start Backend            | venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000           | Dockerfile.api           |
| Start Frontend (dev)     | cd frontend && npm run dev                                                    | frontend/package.json    |
| Build Frontend           | cd frontend && npm run build                                                  | frontend/package.json    |
| Deploy via Docker        | ./deploy.sh                                                                   | deploy.sh                |
| Train PaySim             | venv/bin/python -m src.train_paysim                                           | src/train_paysim.py      |
| Train Bank               | venv/bin/python -m src.train_bank                                             | src/train_bank.py        |
| Train UPI                | venv/bin/python -m src.train_upi                                              | src/train_upi.py         |
| Train Card               | venv/bin/python -m src.train_card                                             | src/train_card.py        |
| Train Bitcoin            | venv/bin/python -m src.train_bitcoin                                          | src/train_bitcoin.py     |
| Train URL Phishing       | venv/bin/python -m src.train_url_phishing                                     | src/train_url_phishing.py|
| Train SMS                | venv/bin/python -m src.train_sms                                              | src/train_sms.py         |
| Train Email              | venv/bin/python -m src.train_email                                            | src/train_email.py       |
| Run Tests                | venv/bin/pytest tests/                                                        | tests/                   |
| Simulate Traffic         | venv/bin/python -m scripts.simulate_traffic                                   | scripts/simulate_traffic.py |
| View Docker Logs         | docker-compose logs -f api                                                    | docker-compose.yml       |
| Free Docker Space        | docker system prune -f                                                        | Docker CLI               |
| Rebuild Containers       | docker-compose build --no-cache                                               | docker-compose.yml       |
| Check API Health         | curl http://localhost:8000/health                                             | api/main.py              |

---

## 22. Start From Zero (No Antigravity)

Follow these steps from a fresh terminal:

    # Step 1: Navigate to project
    cd /Users/zillekibriya/Desktop/Fraud_detection_ml/fraud-detection-ml

    # Step 2: Check project structure
    ls -la

    # Step 3: Check required software
    python3 --version   # Need 3.11+
    node --version      # Need 22+
    docker --version    # Need Docker Desktop running

    # Step 4: Create/activate Python virtual environment
    python3 -m venv venv
    source venv/bin/activate

    # Step 5: Install backend dependencies
    pip install -r requirements.txt

    # Step 6: Install frontend dependencies
    cd frontend && npm install && cd ..

    # Step 7: Configure environment
    cp .env.example .env
    # Edit .env: set ENVIRONMENT, API_KEY, CORS_ORIGINS

    # Step 8: Verify model artifacts exist
    ls models/pre_authorization/   # Must have xgboost_fraud_model.json
    ls models/upi/                 # Must have model.joblib

    # Step 9: If models are missing, train them (requires datasets in dataset/)
    venv/bin/python -m src.train_paysim

    # Step 10: Start the backend
    venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &

    # Step 11: Check backend is healthy
    curl http://localhost:8000/health
    # Expected: {"status":"healthy", ...}

    # Step 12: Start the frontend
    cd frontend && npm run dev &

    # Step 13: Check frontend is running
    open http://localhost:5173

    # Step 14: Test API prediction
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"sms","text":"Your OTP is 123456. Do not share."}'

    # Step 15: Run the test suite
    venv/bin/pytest tests/ -v

    # Step 16: Check logs (Docker)
    docker-compose logs -f api

    # Step 17: Stop the application
    # Manual mode:
    kill $(lsof -ti :8000)   # Stop backend
    kill $(lsof -ti :5173)   # Stop frontend
    # Docker mode:
    docker-compose down

---

## 23. Emergency Recovery

### Model Artifacts Lost

    # Retrain all 8 domain models (requires datasets in dataset/)
    venv/bin/python -m src.train_paysim
    venv/bin/python -m src.train_bank
    venv/bin/python -m src.train_upi
    venv/bin/python -m src.train_card
    venv/bin/python -m src.train_bitcoin
    venv/bin/python -m src.train_url_phishing
    venv/bin/python -m src.train_sms
    venv/bin/python -m src.train_email

### Database Corrupted

    rm -f data/audit_log.db
    # Database recreates automatically on next backend start
    venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

### Docker Out of Disk Space

    # Frees ALL Docker cache, images, and volumes
    docker system prune -a --volumes -f
    # Rebuild
    ./deploy.sh

### Backend Container Crashed

    # Diagnose
    docker-compose logs api | tail -50
    # Restart
    docker-compose restart api

### Dependency Conflict

    # Remove and reinstall venv
    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

---

## 24. Master Cheat Sheet — 20 Most Important Commands

==============================================================
SETUP
==============================================================

    # Create and activate Python virtual environment
    python3 -m venv venv && source venv/bin/activate

    # Install all Python dependencies
    pip install -r requirements.txt

    # Install frontend dependencies
    cd frontend && npm install

==============================================================
RUN (without Docker)
==============================================================

    # Start FraudSense AI backend (FastAPI)
    venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

    # Start React dashboard (development mode)
    cd frontend && npm run dev

    # Build React dashboard for production
    cd frontend && npm run build

==============================================================
DEPLOY (Docker — recommended)
==============================================================

    # Deploy the complete application (all 3 services)
    ./deploy.sh

    # Stop all containers
    docker-compose down

    # Rebuild and redeploy without cache
    docker-compose build --no-cache && docker-compose up -d

==============================================================
TRAIN
==============================================================

    venv/bin/python -m src.train_paysim      # PaySim / Mobile Money
    venv/bin/python -m src.train_bank        # Bank fraud
    venv/bin/python -m src.train_upi         # UPI fraud
    venv/bin/python -m src.train_card        # Credit card fraud
    venv/bin/python -m src.train_bitcoin     # Bitcoin fraud
    venv/bin/python -m src.train_url_phishing # URL phishing
    venv/bin/python -m src.train_sms         # SMS scam
    venv/bin/python -m src.train_email       # Email phishing

==============================================================
TEST
==============================================================

    # Run full Pytest suite
    venv/bin/pytest tests/ -v

    # Run only API tests
    venv/bin/pytest tests/test_api.py -v

    # Simulate API traffic (all domains)
    venv/bin/python -m scripts.simulate_traffic

==============================================================
PREDICT (manual cURL)
==============================================================

    # Health check
    curl http://localhost:8000/health

    # Predict fraud — PaySim suspicious transfer
    curl -X POST http://localhost:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"domain":"paysim","step":1,"type":"TRANSFER","amount":150000.0,"oldbalanceOrg":150000.0,"oldbalanceDest":0.0}'

    # Scan suspicious URL
    curl -X POST http://localhost:8000/api/v1/scans/url \
      -H "Content-Type: application/json" \
      -d '{"url":"http://fake-bank-login.example/verify"}'

    # Analyze scam SMS
    curl -X POST http://localhost:8000/api/v1/scans/sms \
      -H "Content-Type: application/json" \
      -d '{"text":"Your account is blocked. Click http://evil.com to restore."}'

==============================================================
LOGS AND DEBUG
==============================================================

    # Stream backend logs (Docker)
    docker-compose logs -f api

    # Stream frontend logs (Docker)
    docker-compose logs -f frontend

    # Access backend container shell
    docker exec -it fraud-detection-ml-api-1 bash

    # Free Docker disk space (fixes Read-Only FS errors)
    docker system prune -f

==============================================================
DATABASE
==============================================================

    # Reset audit database (DANGER: deletes all data)
    rm -f data/audit_log.db

==============================================================
GIT
==============================================================

    # Commit all changes
    git add . && git commit -m "feat: description"

    # Push to remote
    git push origin main

==============================================================

Verified source files:
  api/routes.py, api/case_routes.py, api/monitoring_routes.py,
  api/intelligence_routes.py, api/main.py, api/security.py, api/schemas.py,
  src/train_paysim.py, src/train_bank.py, src/train_upi.py, src/train_card.py,
  src/train_bitcoin.py, src/train_url_phishing.py, src/train_sms.py, src/train_email.py,
  scripts/simulate_traffic.py, tests/test_api.py,
  frontend/package.json, frontend/nginx.conf, frontend/vite.config.ts,
  docker-compose.yml, Dockerfile.api, Dockerfile.frontend, Dockerfile.ui,
  deploy.sh, requirements.txt, requirements-dev.txt,
  .env.example, .dockerignore, models/model_registry.json

