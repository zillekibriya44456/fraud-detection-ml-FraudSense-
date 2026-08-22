# Research Questions

Based on the actual implemented system (Steps 1-7), the following research questions are formulated.

### RQ1: How does leakage-aware pre-authorization feature selection affect fraud detection system design?
- **Motivation**: Most academic papers on PaySim use `newbalanceOrig` to achieve near-perfect F1-scores. In reality, this data is unavailable before authorization.
- **Experimental Evidence Available**: We have the active Pydantic schema validation that physically prevents `newbalanceOrig` from entering the inference pipeline.
- **Evaluation Method**: Architectural analysis of the API enforcement layer.
- **Limitations**: We do not yet have comparative F1-scores of Leakage vs. No-Leakage (requires Step 8 execution).

### RQ2: How do Logistic Regression, Random Forest, and XGBoost compare under strict pre-authorization constraints?
- **Motivation**: To prove that XGBoost remains superior even when future-leaking features are removed.
- **Experimental Evidence Available**: **NONE (MISSING)**. Step 8 was not executed.
- **Evaluation Method**: N/A.
- **Limitations**: Cannot be answered until Step 8 is executed.

### RQ3: Can a context-aware APPROVE / VERIFY / BLOCK decision framework provide a more operationally useful outcome than binary classification?
- **Motivation**: Binary blocking creates high friction. Step-up verification (MFA/OTP) mitigates False Positives.
- **Experimental Evidence Available**: The implemented `DecisionEngine` and E2E simulation logs showing high-risk transactions being routed to `VERIFY`.
- **Evaluation Method**: Analysis of the rule-based thresholds and state transitions in `api/services.py`.
- **Limitations**: Evaluation is currently simulated; we lack a live A/B test of friction reduction.

### RQ4: What are the limitations of behavioral fraud analysis under sparse transaction history?
- **Motivation**: PaySim senders transact rarely (99.85% transact once).
- **Experimental Evidence Available**: The `BehavioralEngine` explicitly outputs `NONE`, `LIMITED`, and `SUFFICIENT` states based on historical counts.
- **Evaluation Method**: Statistical summary of the dataset's sparsity and the architectural fallback to "NONE".
- **Limitations**: We cannot prove that behavioral features actually catch fraud in PaySim because history is too sparse to evaluate empirically.
