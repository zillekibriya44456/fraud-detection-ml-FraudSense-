# Behavioral Risk Limitations

## 1. The Sparsity of PaySim
An extensive audit of the PaySim dataset (documented in `STEP_3_BEHAVIORAL_RISK_REPORT.md`) revealed a severe limitation for behavioral profiling:
- **99.85%** of senders (`nameOrig`) only transact **once** in the entire dataset.

## 2. The Cold-Start Problem
In real banking environments, users have rich transaction histories (e.g., average daily spend, typical locations). In PaySim, attempting to calculate an "average transaction amount" for a user fails 99.85% of the time, resulting in a cold-start.

## 3. Honest Engineering Solution
Rather than hallucinating historical data or artificially copying rows to create fake histories, FRAUDSENSE AI implements an explicit state machine in the `BehavioralEngine`:
- **NONE**: User has 0 previous transactions.
- **LIMITED**: User has <3 previous transactions.
- **SUFFICIENT**: User has >=3 previous transactions.

If a user has `NONE`, the behavioral risk score defaults to 0.0, and the decision engine relies entirely on the XGBoost prediction.

## 4. Limitation for Academic Publication
We cannot claim that "Behavioral velocity tracking significantly improves fraud detection in our experiments", because the dataset mathematically cannot support that claim. 

Instead, the contribution is **methodological**: we provide a robust architecture that safely handles cold-start users without crashing or throwing false positives.
