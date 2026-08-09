# FraudGuard AI
**Fraud Detection in Financial Transactions Using Machine Learning**

## Project Overview
FraudGuard AI is a practical, intelligent, explainable, and secure real-time financial fraud detection platform. It is designed to detect suspicious financial transactions, calculate their risk level, explain why a transaction was flagged, and support human decision-making. 

## Problem Statement
Financial transactions through online banking, digital wallets, and e-commerce are rapidly increasing, creating a large attack surface for fraud. Traditional rule-based systems struggle to adapt to evolving fraud patterns. Furthermore, the extreme class imbalance in financial datasets makes accurate detection difficult. False negatives result in financial loss, while false positives block legitimate users. A modern system must not only detect fraud but explain *why* it was detected to aid investigators.

## Vision and Mission
**Vision:** Evolve into a research-grade machine learning system, a real-time detection platform, and an explainable AI architecture that bridges the gap between theoretical models and production-ready software.
**Mission:** Reduce financial fraud by combining behavioral transaction analysis, advanced class-imbalance handling, anomaly detection, and explainable AI with real-time APIs and secure deployment.

## Proposed Pipeline
1. Input Validation
2. Data Preprocessing
3. Behavioral Feature Engineering
4. Class-Imbalance Handling
5. Machine Learning Prediction & Anomaly Detection
6. Risk Scoring (Low / Medium / High)
7. Explainable AI (e.g., SHAP)
8. Decision (Approve / Review / Alert / Block)
9. Database + Audit Log
10. Monitoring & Human Feedback

## Planned Machine Learning Strategy
The project will evaluate multiple algorithms to find the best balance of recall, precision, and latency, rather than relying solely on accuracy. 
- **Baseline:** Logistic Regression
- **Advanced Models:** Decision Tree, Random Forest, XGBoost, Support Vector Machine (SVM)
- **Anomaly Detection:** Isolation Forest

## Dataset
The project utilizes the **PaySim** dataset, a synthetic dataset of mobile money transactions. It is widely used in academic research because it provides non-anonymized, interpretable features (such as `amount`, `oldbalanceOrg`, `newbalanceOrig`) which are essential for behavioral feature engineering and Explainable AI (SHAP). 
Detailed dataset documentation can be found in `docs/dataset.md`.

## Evaluation Metrics
Primary fraud-focused metrics:
- Recall
- Precision
- F1-score
- PR-AUC (Precision-Recall Area Under Curve)

## Technology Stack
- **Data/ML:** Python, Pandas, NumPy, Scikit-learn, XGBoost, imbalanced-learn
- **Explainability:** SHAP
- **Frontend:** Streamlit
- **Backend/API:** FastAPI, Uvicorn
- **Testing:** Pytest
- **Containerization:** Docker

## Development Roadmap
This project is developed incrementally. Refer to the internal documentation (`docs/project_plan.md`) for detailed phase breakdowns, from environment setup to final deployment and research paper documentation.

## License
[License to be finalized]
