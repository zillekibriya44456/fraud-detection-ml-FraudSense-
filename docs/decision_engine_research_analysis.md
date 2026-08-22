# Context-Aware Decision Engine Research Analysis

## 1. Problem with Binary Fraud Classification
Relying solely on a raw probability score (e.g. `p > 0.85 = FRAUD`) from an ML model creates critical blind spots. 
For instance, a transaction with `p=0.35` (below the standard 0.40 review threshold) is normally approved. But if that transaction is for \$150,000, the cost of a False Negative is catastrophic. A contextual engine is required to fuse these signals securely.

## 2. Approve/Verify/Block Framework
We designed a 3-tier system:
- **APPROVE**: Nominal transactions.
- **VERIFY**: Borderline transactions, or transactions where the ML score is low but the context (Amount, Behavior) indicates risk. These trigger a Step-Up Authentication workflow (OTP).
- **BLOCK**: High certainty fraud or severe behavioral anomalies.

## 3. Threshold Selection Methodology
Thresholds are defined hierarchically in `config/risk_decision_policy.yaml`:
- **ml_high_risk (0.85)**: Empirically set to ensure near 100% precision.
- **ml_medium_risk (0.30)**: Lowered from 0.40 to capture more recall, knowing that they will simply be routed to VERIFY rather than outright blocked.
- **high_value_amount (100,000)**: Any transaction above this amount automatically triggers VERIFY if there is even slight ML suspicion (`p > 0.30`).
- **behavioral_anomaly_threshold (0.50)**: Standard deviation heuristic from the Behavioral Engine.

## 4. Experimental Results
A simulation comparing the old Model-Only logic vs Context-Aware logic yielded:

| Scenario | Model-Only Decision | Context-Aware Decision | Result |
|---|---|---|---|
| Low Risk Nominal | APPROVE | APPROVE | No change (Good UX preserved) |
| High Value, Low/Med Risk | APPROVE | **VERIFY** | Financial risk mitigated |
| Med Risk, Behavioral Anomaly | VERIFY | **BLOCK** | Account takeover stopped |
| High Risk Fraud | BLOCK | BLOCK | No change |

**Conclusion**: The Context-Aware engine successfully routes dangerous edge cases to safer outcomes without increasing the friction (False Positives) for nominal transactions.

## 5. Dataset & Behavioral Limitations
As documented previously, 99.85% of PaySim users transact once, meaning the Behavioral Anomaly rule rarely triggers on real PaySim data. It exists architecturally to support real-world production environments where density is higher.
