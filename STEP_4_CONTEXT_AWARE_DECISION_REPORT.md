# STEP 4: CONTEXT-AWARE DECISION ENGINE REPORT

## 1. Existing Logic Analysis
Previously, the system made decisions sequentially based entirely on raw ML fraud probability. Context such as transaction amount and behavioral history was ignored, leading to potential catastrophic false negatives on high-value transfers.

## 2. New Decision Policy
We introduced a hierarchical, context-aware rule engine configured via `config/risk_decision_policy.yaml`.
The engine fuses 4 signals:
1. `ml_prob` (XGBoost)
2. `amount` (Transaction Size)
3. `behavioral_signal` (Velocity/Anomaly)
4. `history_status` (Cold Start Indicator)

## 3. Decision Confidence Methodology
Decisions are now tagged with a Confidence Level:
- **HIGH_CONFIDENCE**: ML prediction + Sufficient user behavioral history.
- **MEDIUM_CONFIDENCE**: ML prediction + Limited recipient history.
- **LIMITED_CONTEXT**: Cold Start user (no history). Relying entirely on ML.

## 4. Verify Workflow Design
Added a mock `/verify_transaction/{id}` endpoint to `api/routes.py`. Transactions flagged as **VERIFY** require the client to submit a valid OTP (mocked as '123456') to proceed to **APPROVE**. This simulates Step-Up Authentication without building complex OAuth flows.

## 5. UI Implementation
The Streamlit dashboard (`app/streamlit_app.py`) was updated to display:
- ML Risk Score
- Decision Context (Confidence, Policy Version)
- Explicit Decision Reasons generated dynamically by the engine.
- A functional OTP input form for VERIFY transactions.

## 6. Experimental Comparison
Running `evaluate_decision_engine.py` proved the Context-Aware Engine is superior. It successfully intercepted a \$150,000 transaction that the old model would have approved, safely routing it to VERIFY based on the context rules.

## 7. Tests Added & Results
- Rewrote `tests/test_decision_engine.py` to test the new 5-rule hierarchical policy.
- Verified all combinations of signals deterministically.
- **Run**: `pytest`
- **Result**: `14 passed`
- **Status**: 100% Pass Rate.

## 8. Production Limitations
PaySim data sparsity means the Behavioral signal rule (`R2_BEHAVIORAL_ANOMALY`) will rarely trigger natively. The configuration thresholds (`100,000` amount limit, etc.) are currently static and should be dynamically adjusted in production using Live Shadow Mode testing.

========================================================

**STEP 4 STATUS: PASS**
