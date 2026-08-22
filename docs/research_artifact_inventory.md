# Research Artifact Inventory

## 1. Existing Artifacts (Steps 1-7)

| ARTIFACT NAME | LOCATION | PURPOSE | REAL RESULT AVAILABLE? | CAN BE USED IN RESEARCH PAPER? | LIMITATIONS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `xgboost_fraud_model.json` | `models/` | Active production prototype model. | YES | YES | Trained via random split, not temporal. |
| `test_behavioral.py` | `tests/` | Verifies behavioral cold-start handling. | YES | YES | Unit test, not empirical performance test. |
| `e2e_simulation.py` | `scripts/` | Verifies system latency and routing. | YES | YES | Measures system latency, but on synthetic local traffic. |
| `drift_analyzer.py` | `src/monitoring/` | Calculates PSI. | YES | YES | Uses baseline distribution from train split. |
| `final_system_architecture.md` | `docs/` | Documents end-to-end system flow. | YES | YES | Perfect for Architectural Figure generation. |
| `performance_test.py` | `scripts/` | Measures API throughput. | YES | YES | Tests SQLite bottlenecks, useful for limitations section. |

## 2. Missing Artifacts (Step 8 Bypass)

> [!WARNING]
> The execution of Step 8 (Scientific Model Comparison) was bypassed. Therefore, the following artifacts do not exist.

| ARTIFACT NAME | LOCATION | PURPOSE | REAL RESULT AVAILABLE? | CAN BE USED IN RESEARCH PAPER? | LIMITATIONS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `experimental_results.json` | `artifacts/experiments/` | Store precision/recall for alternative models. | **NO** | **NO** | Missing entirely. |
| `pr_curves.png` | `results/figures/` | Visual comparison of PR-AUC. | **NO** | **NO** | Missing entirely. |
| `threshold_optimization.csv` | `results/` | Optimal thresholds per model. | **NO** | **NO** | Missing entirely. |
| `temporal_split.py` | `src/` | Temporal train/val/test data splitting. | **NO** | **NO** | Missing entirely. |
