# FRAUD DETECTION IN FINANCIAL TRANSACTIONS USING MACHINE LEARNING

## ABSTRACT
**Version A (Technical Academic)**
We present FRAUDSENSE AI, an end-to-end engineering prototype for real-time pre-authorization financial fraud detection. Utilizing the PaySim dataset, we demonstrate the critical necessity of leakage-aware feature selection by strictly enforcing the exclusion of post-transaction balances at the API layer. To mitigate the friction of binary ML classification, we introduce a context-aware tri-state decision engine (APPROVE/VERIFY/BLOCK) that safely handles the severe sparsity of behavioral histories via fallback states. Our architecture integrates live precision tracking via delayed case resolutions and asynchronous drift monitoring. However, quantitative evaluation of alternative models is currently missing, requiring further experimental execution before publication.

**Version B (IEEE Conference Style)**
Financial fraud detection models often report artificially high F1-scores by evaluating on post-transaction features unavailable during real-time pre-authorization. This paper introduces FRAUDSENSE AI, a robust prototype enforcing strict schema-level data leakage prevention. We propose an operational APPROVE/VERIFY/BLOCK decision routing framework, bridging the gap between raw ML probabilities and business friction, alongside an explicit cold-start handler for sparse behavioral datasets. The system is fully containerized with integrated model drift and case management. Complete temporal-split experiments comparing Random Forest and XGBoost are pending.

**Version C (Simple and Clear)**
This project builds a complete, real-time system to detect fraud in financial transactions before the money is moved. Many academic models cheat by looking at data that isn't available yet; we built a strict API that prevents this. Instead of just saying "Fraud" or "Not Fraud," the system can ask the user for verification (like a text message) if it's unsure. It also handles users who have no transaction history safely. We still need to run our final experiments to prove which machine learning model works best for this setup.

## KEYWORDS
Fraud Detection, Machine Learning, Data Leakage, MLOps, Pre-Authorization, XGBoost, PaySim

---

## I. INTRODUCTION
*(Introduction to the challenge of real-time fraud detection vs offline analysis)*

## II. RELATED WORK
*(To be completed: LITERATURE VERIFICATION REQUIRED)*

## III. PROBLEM STATEMENT AND RESEARCH GAP
Most academic evaluations on PaySim suffer from post-transaction data leakage. Furthermore, operational integration of binary classifiers into banking systems causes severe friction via false positives.

## IV. SYSTEM METHODOLOGY
### A. Dataset and Feature Constraints
PaySim dataset. Filtered to TRANSFER and CASH_OUT.

### B. Leakage-Aware Pre-Authorization Validation
Exclusion of `newbalanceOrig` and `newbalanceDest`. Pydantic schema enforcement.

### C. Machine Learning Models
*(Currently only XGBoost baseline evaluated. Temporal split experiments pending.)*

### D. Behavioral Risk Analysis
Explicit tagging of `NONE`, `LIMITED`, and `SUFFICIENT` history to combat PaySim's 99.85% sparsity rate.

### E. Context-Aware Decision Engine
APPROVE / VERIFY / BLOCK threshold routing.

### F. Fraud Alert and Case Management
SQLite-backed analyst queue with resolution-driven live precision monitoring.

### G. Model Monitoring and Drift Detection
Asynchronous PSI calculations.

## V. EXPERIMENTAL SETUP
*(MISSING: Step 8 Execution required to document temporal split methodology and class imbalance weighting.)*

## VI. RESULTS AND DISCUSSION
*(MISSING: Awaiting Step 8 results for PR-Curves, Threshold analysis, and Model Comparison tables.)*

## VII. LIMITATIONS
- PaySim is synthetic; findings may not generalize to real banking systems.
- PaySim does not represent actual UPI, credit card, or net banking channels.
- Behavioral history is extremely sparse (99.85% single transactions).
- Step-up verification is simulated.
- SQLite is used as a prototype-level database.

## VIII. CONCLUSION AND FUTURE WORK
*(To be written after experiments are concluded.)*

## REFERENCES
*(REFERENCES TO BE VERIFIED)*
