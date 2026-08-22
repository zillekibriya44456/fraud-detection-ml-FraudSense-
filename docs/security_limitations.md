# Security Limitations

## Overview
FRAUDSENSE AI is currently a **Research and Engineering Prototype**. It is NOT a production-ready core banking system. The following limitations explicitly define the boundaries of the prototype's current security posture.

## 1. Network & Infrastructure Security
- **No TLS Termination**: The FastAPI backend communicates via HTTP over port 8000. In production, this must run behind a reverse proxy (e.g., NGINX, AWS API Gateway) with TLS 1.3 termination.
- **No VPC Isolation**: The prototype assumes the database and API are running on the same network namespace without subnets.
- **No WAF**: There is no Web Application Firewall to protect against Layer 7 attacks (SQLi, XSS, DDoS).

## 2. Authentication & Authorization
- **Unauthenticated API**: The `POST /predict`, `/cases`, and `/monitoring` endpoints are completely open.
- **Simulated Verification**: The `POST /verify_transaction` endpoint accepts a hardcoded OTP (`123456`). This must be replaced with a real SMS/Email OTP provider (e.g., Twilio, AWS SNS).

## 3. Data Protection
- **Cleartext Database**: The SQLite database (`audit_log.db`) is not encrypted at rest. PII and financial metadata are stored in cleartext.
- **No Data Masking**: Analyst views do not mask PII (e.g., showing the last 4 digits of an account number).

## 4. Availability & Reliability
- **SQLite Concurrency**: SQLite utilizes file-level locking. Under high concurrency (>100 req/sec sustained), it will experience `database is locked` errors, causing requests to fail.
- **Single Point of Failure**: The model and API are tightly coupled in a single container. 

## 5. ML Specific Security
- **Model Poisoning**: The drift monitoring detects changes, but there is no explicit defense against an adversary intentionally probing the API to map the decision boundary (Model Inversion/Extraction).
- **Data Leakage**: We implemented feature availability checks, but the synthetic nature of the PaySim dataset means real-world data pipelines might introduce unseen leakages.
