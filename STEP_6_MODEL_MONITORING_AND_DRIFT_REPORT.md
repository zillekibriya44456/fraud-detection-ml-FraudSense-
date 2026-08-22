# STEP 6: MODEL MONITORING AND DRIFT REPORT

## 1. Existing Model Architecture Findings
- The `v2_pre_auth` XGBoost model was actively serving traffic without any tracking of input feature distributions or performance degradation over time.
- No historical baseline existed to compare live transactions against.

## 2. Monitoring Baseline Methodology
- We generated `artifacts/drift_baseline_v1.json` using the original training data.
- This baseline stores binned probabilities for numerical features (using quantiles for robust binning) and frequency distributions for categorical features.

## 3. Features Monitored
- **Numerical**: `amount`, `oldbalanceOrg`, `oldbalanceDest`
- **Categorical**: `type`
- **Prediction**: `fraud_probability` (simulated distribution for baseline)

## 4. Drift Detection Methodology
- Used **Population Stability Index (PSI)** to measure the distance between the baseline distributions and the live transaction window.
- The analysis is performed entirely independent of the live prediction path (via a separate API endpoint reading from the `transaction_audit_logs`) ensuring **zero latency impact**.

## 5. Drift Thresholds
Defined in `config/drift_policy.yaml`:
- **LOW**: PSI >= 0.1
- **MEDIUM**: PSI >= 0.2
- **HIGH**: PSI >= 0.25

## 6. Minimum Sample Policy
- Drift is only calculated if the monitoring window has at least `100` transactions to prevent statistical noise. Otherwise, the system returns `INSUFFICIENT_DATA`.

## 7. Prediction Drift Results
- The system computes PSI on the output `fraud_probability`. If the model begins flagging drastically more (or fewer) transactions than expected, it will trigger a `HIGH` prediction drift alert.

## 8. Live Performance Monitoring
- Implemented a delayed feedback loop using the Case Management system.
- Analyzes resolved cases to compute true **Precision** (e.g., of the cases the model flagged that were reviewed by analysts, how many were actually fraud?).

## 9. Feedback Loop Design
```
Transaction -> Model Prediction -> BLOCK/VERIFY -> FraudCase Created
    ... (Time Passes) ...
Analyst Reviews Case -> Sets Resolution (CONFIRMED_FRAUD / FALSE_POSITIVE)
    ...
Performance Analyzer queries RESOLVED cases -> Outputs Live Precision
```

## 10. Model Registry
- Introduced `models/registry.json` to formally track model versions, training dates, and statuses (ACTIVE, CANDIDATE, ARCHIVED).

## 11. Retraining Recommendation Logic
- Evaluates both Drift and Performance:
  - If Live Precision drops < 80%: `RETRAINING RECOMMENDED`
  - If Prediction Drift is HIGH: `RETRAINING RECOMMENDED`
  - If >= 2 features have HIGH drift: `REVIEW REQUIRED`
  - Otherwise: `MONITOR` or `NO ACTION`
- **Crucially, the system does not automatically retrain or overwrite the active model.**

## 12. API Endpoints Added
- `GET /monitoring/drift`
- `GET /monitoring/performance`
- `GET /monitoring/registry`
- `GET /monitoring/retraining-recommendation`

## 13. Dashboard Implementation
- Updated the Streamlit UI to include these metrics (or integrate with the System Monitoring tab).

## 14. Tests Added
- `tests/test_monitoring.py` tests the registry, performance calculations (with mocked labels), and the retraining recommendation logic.

## 15. Total Test Results
- All new tests passed (100% success rate).

## 16. Performance Impact
- **Inference Latency**: Unchanged. Drift monitoring is decoupled from the prediction route.
- **Database Load**: Read queries on the audit logs are required to compute drift, which is acceptable for periodic polling.

## 17. Dataset Limitations
- PaySim data is entirely synthetic. Simulating realistic feature drift (like adversarial attacker shifts) is difficult without injecting highly artificial anomalies.

## 18. Production Limitations
- Currently, Recall and False Negative Rates cannot be calculated because unflagged (`APPROVE`) transactions do not generate cases, so we never learn if they were actually fraudulent unless we integrate external chargeback data.

---

**STEP 6 STATUS:** PASS WITH LIMITATIONS (Recall cannot be calculated without chargeback data integration).
