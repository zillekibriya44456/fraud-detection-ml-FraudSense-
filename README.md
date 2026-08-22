# ⚡ FraudSense AI

> **Detect. Analyze. Prevent.**  
> An enterprise-grade, real-time Pre-Authorization Machine Learning pipeline for financial fraud detection.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35.0-FF4B4B?logo=streamlit)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0.3-orange)
![SHAP](https://img.shields.io/badge/XAI-SHAP-purple)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)

FraudSense AI is a complete end-to-end Machine Learning system designed to intercept and analyze financial transactions **before** authorization. By excluding post-transaction leakage features (like updated account balances), the model operates in a true real-time capacity, making decisions based on transaction velocity, historical baseline anomalies, and categorical risk.

## 🚀 Key Features

- **Real-Time Pre-Authorization ML**: Zero data leakage. Evaluates risk instantly based strictly on pre-transaction data.
- **Explainable AI (XAI)**: Integrated `SHAP` TreeExplainer provides live, feature-level attribution explaining *why* a transaction was blocked.
- **Configurable Decision Engine**: YAML-based risk routing (Low, Medium, High) triggering configurable actions (Approve, Verify, Block).
- **Payment Channel Architecture**: Abstracted adapter layer easily extensible for `UPI`, `Credit Card`, and `Net Banking` payloads.
- **High-Performance API**: Built with `FastAPI`, scaling efficiently for bulk JSON processing.
- **Cybersecurity Command Center**: A premium `Streamlit` dashboard for human-in-the-loop analysis and system monitoring.
- **Automated Audit Logging**: SQLite integration (swappable for PostgreSQL) tracking every prediction, latency, and Fraud Alert.

---

## 🛠️ Tech Stack

- **Machine Learning**: `scikit-learn`, `xgboost`, `pandas`, `shap`
- **Backend API**: `FastAPI`, `Uvicorn`, `Pydantic`
- **Database**: `SQLAlchemy`, `SQLite`
- **Frontend UI**: `Streamlit`, `Plotly`
- **Deployment**: `Docker`, `Docker Compose`

---

## 🐳 Quick Start (Docker)

The absolute fastest way to run the entire system is via Docker Compose.

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/fraud-detection-ml.git
cd fraud-detection-ml

# 2. Build and launch the cluster
docker-compose up --build
```

The services will be available at:
- **Cyber Dashboard (UI)**: [http://localhost:8501](http://localhost:8501)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 💻 Manual Setup (Local Development)

If you prefer to run the system directly on your machine:

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the FastAPI Backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 &

# 4. Start the Streamlit Frontend
streamlit run app/streamlit_app.py --server.port=8501
```

---

## 🔬 Architecture Diagram

```text
[ Raw Transaction Payload ] --> (FastAPI Router)
                                      |
                               [ Channel Adapter ] (Normalizes UPI/CC to generic schema)
                                      |
                           [ Feature Engineering ] (Calculates velocity/ratios)
                                      |
                                [ XGBoost Model ] --> (SHAP Explainer)
                                      |
                             [ Decision Engine ] (Reads config/risk_thresholds.yaml)
                                      |
                 +--------------------+--------------------+
                 |                    |                    |
             APPROVE                VERIFY               BLOCK
            (Low Risk)          (Medium Risk)         (High Risk -> FraudAlert DB)
```

---

## 📊 Experimental Results

The dual-model experimentation phase proved that relying on "post-transaction" features artificially inflated Accuracy to 99.9%. By strictly limiting the model to "pre-authorization" features, we built a mathematically sound real-time engine:

| Model | Precision | Recall | F1 Score | PR-AUC |
|-------|-----------|--------|----------|--------|
| **XGBoost (Real-Time)** | 91.2% | 85.4% | 88.2% | 0.901 |

*(Metrics dynamically loaded into the UI from `artifacts/metrics/model_comparison.json`)*

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/fraud-detection-ml/issues).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
