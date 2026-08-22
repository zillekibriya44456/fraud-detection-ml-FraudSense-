# Authentication & Authorization Roadmap

## Current State
The FRAUDSENSE AI prototype currently operates **without** authentication. Endpoints are fully open, which is acceptable for a local engineering prototype but fundamentally insecure for production deployment.

## Required Roles
A production deployment must clearly separate the following roles:

### 1. Payment Client (Service-to-Service)
- **Scope**: Internal microservices (e.g., Payment Gateway, Core Banking) calling `POST /predict`.
- **Authentication**: mTLS (Mutual TLS) and long-lived API Keys or Service Account JWTs.
- **Authorization**: Allowed to submit transactions and receive predictions. Denied access to Case Management, Monitoring, and auditing.

### 2. Fraud Analyst (Human User)
- **Scope**: Human investigators using the Streamlit Dashboard.
- **Authentication**: Single Sign-On (SSO) via OAuth2/OIDC (e.g., Okta, Azure AD) integrating with the bank's identity provider.
- **Authorization**: Allowed to view `GET /cases`, transition case statuses via `PATCH /cases/{id}/status`, and view model monitoring. Denied access to direct transaction prediction endpoints.

### 3. Administrator / Data Scientist (Human User)
- **Scope**: Advanced configuration and model maintenance.
- **Authentication**: SSO with Multi-Factor Authentication (MFA).
- **Authorization**: Allowed to trigger model retraining, update drift policies, and archive cases.

## Proposed Implementation (Future Phase)
1. Integrate `fastapi.security.OAuth2PasswordBearer` and `SecurityScopes` into FastAPI.
2. Require JWT validation on all `/cases` and `/monitoring` endpoints.
3. Require `X-API-KEY` validation for the `/predict` endpoints.
4. Integrate Streamlit with an Identity Provider using libraries like `authlib`.
