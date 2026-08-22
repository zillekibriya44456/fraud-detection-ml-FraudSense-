# Final Paper Claim Validation

| CLAIM | EVIDENCE | VALID? |
| :--- | :--- | :--- |
| **"enforcing strict schema-level data leakage prevention"** | Checked `api/schemas.py`. `TransactionRequest` explicitly excludes `newbalanceOrig` and `newbalanceDest`. | **YES** |
| **"APPROVE/VERIFY/BLOCK decision routing framework"** | Checked `api/services.py`. `FraudService.evaluate_decision_policy` returns these three states based on YAML thresholds. | **YES** |
| **"explicit cold-start handler for sparse behavioral datasets"** | Checked `src/behavioral/engine.py`. Implements `HistoryStatus.NONE` for users with no prior records. | **YES** |
| **"PaySim extreme sparsity (99.85%)"** | Checked `STEP_3_BEHAVIORAL_RISK_REPORT.md` which documented this exact statistical finding. | **YES** |
| **"API sustains ~118 requests/second"** | Checked output of `task-954` (`scripts/performance_test.py`), which recorded exactly 118.97 req/sec. | **YES** |
| **"Complete temporal-split experiments... remain pending"** | Acknowledges the bypass of Step 8. | **YES** |

*All fabricated claims, references, and missing experiments were successfully purged or marked as pending.*
