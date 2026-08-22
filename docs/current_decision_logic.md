# Current Decision Logic Analysis

## 1. Current Fraud Thresholds
The system relies on fixed, global thresholds loaded from `config/risk_thresholds.yaml`.
- **Medium Risk Threshold**: 0.40
- **High Risk Threshold**: 0.85

## 2. Current Risk Levels & Decisions
The logic in `src/decision_engine.py` is purely sequential based on ML probability:
- **`fraud_probability` < 0.40**: LOW Risk $\rightarrow$ APPROVE
- **`fraud_probability` $\ge$ 0.40 and < 0.85**: MEDIUM Risk $\rightarrow$ VERIFY
- **`fraud_probability` $\ge$ 0.85**: HIGH Risk $\rightarrow$ BLOCK

## 3. Signal Utilization
| Signal | Currently Influences Decision? |
|---|---|
| ML fraud_probability | YES |
| Behavioral Risk Signal | NO |
| Behavioral History Status | NO |
| Transaction Amount | NO |
| Transaction Type | NO |

## 4. Limitations Identified
1. **No Behavioral Fusion**: The behavioral engine was built in Step 3 but is currently entirely ignored by the decision-maker. 
2. **Context-Blind**: A $10.00 uncertain transaction is treated identically to a $10,000.00 uncertain transaction, leading to sub-optimal verification routing.
3. **No Confidence Scoring**: The system lacks a measure of confidence based on history availability (Cold Start).
4. **Hardcoded Threshold Bounds**: There is no flexibility to route an uncertain high-value transaction differently from a low-value one.
