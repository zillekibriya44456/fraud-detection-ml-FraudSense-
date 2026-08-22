# Research Contribution Analysis

## A. Methodological Contributions

### 1. Leakage-Aware Pre-Authorization Architecture
- **Type**: Methodological & Engineering
- **Evidence**: Explicit removal of `newbalanceOrig`/`newbalanceDest` and Pydantic API air-gapping.
- **Novelty**: High. Many PaySim papers report 0.99 F1-scores by illegally utilizing post-transaction data. This project proves that enforcing pre-authorization constraints requires architectural defenses, not just script changes.
- **Limitations**: We currently lack the quantitative F1-score drop comparison (Step 8 missing).

### 2. Context-Aware Decision Framework (APPROVE/VERIFY/BLOCK)
- **Type**: System Architecture Contribution
- **Evidence**: `DecisionEngine` implementation fusing ML probability + Behavioral Risk into a tri-state action.
- **Novelty**: Moderate to High. Academic literature heavily focuses on binary ML outputs. Bridging ML probabilities to operational friction tiers (Step-up auth) is a major contribution.
- **Limitations**: Simulated verification; no live A/B test data.

### 3. Explicit Handling of Cold-Start Behavioral Sparsity
- **Type**: Methodological
- **Evidence**: `BehavioralEngine`'s explicit `NONE`, `LIMITED`, `SUFFICIENT` historical tagging.
- **Novelty**: Moderate.
- **Limitations**: Due to PaySim's extreme sparsity, the engine mostly operates in fallback mode.

## B. Engineering Contributions

### 4. Delayed-Label Precision Monitoring
- **Type**: Engineering Integration
- **Evidence**: The system links `TransactionAuditLogs` with `CaseResolutions` to calculate live precision dynamically, avoiding the trap of assuming real-time ground truth.
- **Novelty**: High. This mirrors real-world MLOps where fraud chargebacks are delayed by 30-90 days.
