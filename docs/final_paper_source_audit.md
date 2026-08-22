# Final Paper Source Audit

| CLAIM | SOURCE | EVIDENCE AVAILABLE? | SAFE TO INCLUDE? | LIMITATIONS |
| :--- | :--- | :--- | :--- | :--- |
| **Leakage Prevention at API Layer** | `api/schemas.py`, `src/preprocessing.py` | YES | YES | None. The schema validation actively prevents post-transaction variables. |
| **Tri-State Decision Engine** | `api/services.py`, `e2e_simulation.py` | YES | YES | Simulated results only. We do not have actual user-interaction data for the `VERIFY` flow. |
| **Behavioral Cold-Start Handling** | `src/behavioral/engine.py` | YES | YES | Only theoretical/architectural, as 99.85% of the PaySim dataset triggers the `NONE` state fallback. |
| **XGBoost Performance Superiority** | N/A (Step 8 Bypassed) | **NO** | **NO** | Cannot claim XGBoost is the best model without executing the comparative experiments in Step 8. |
| **High API Throughput** | `scripts/performance_test.py` | YES | YES | Restricted to single-node SQLite limitations (~118 req/sec). Not banking grade. |
| **Asynchronous Drift Monitoring** | `src/monitoring/drift_analyzer.py` | YES | YES | Only tested on simulated audit logs; lacks real live drift distribution shifts. |
