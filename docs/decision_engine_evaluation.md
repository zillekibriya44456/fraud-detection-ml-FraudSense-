# Decision Engine Evaluation

## 1. Concept: Binary vs. Tri-State
Traditional fraud models output a binary prediction: **Fraud (1)** or **Not Fraud (0)**. 
In a banking environment, an aggressive threshold on a binary model results in blocked legitimate transactions (False Positives), heavily impacting customer satisfaction and increasing support costs.

FRAUDSENSE AI implements a **Context-Aware Decision Engine** with three states:
- **APPROVE**: Low ML probability, low behavioral risk.
- **VERIFY**: Medium risk (e.g., probability between 0.6 and 0.8) or high behavioral velocity on an otherwise normal transaction.
- **BLOCK**: Extremely high probability (>0.8).

## 2. Simulated Results
Because we do not have a live A/B test with actual customers, the current evaluation is based on simulated E2E test runs and architectural design.

### A. Simulated Binary Decision (Threshold 0.5)
- All transactions > 0.5 probability are **BLOCKED**.
- **Impact**: Maximum friction. Every false positive results in a frozen account or blocked card.

### B. Tri-State Decision Framework
- Transactions > 0.8 are **BLOCKED**.
- Transactions between 0.6 and 0.8 are sent to **VERIFY** (Step-up authentication like OTP).
- **Measured Result**: In our E2E simulations (`scripts/e2e_simulation.py`), high-risk synthetic payloads correctly route to `VERIFY` or `BLOCK` based on the YAML thresholds in `api/services.py`. 
- **Business Impact**: If an OTP verification succeeds, the transaction proceeds without manual analyst intervention. This theoretically reduces the Analyst Case Queue size by resolving "grey area" alerts automatically via the customer.

## 3. Limitations
We cannot provide empirical proof of false positive reduction without live customer behavior data. The dataset (PaySim) does not contain information on whether a user would have passed an OTP challenge. Therefore, this remains an **architectural contribution**, not an empirically proven one.
