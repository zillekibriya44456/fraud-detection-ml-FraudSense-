# FRAUD DETECTION IN FINANCIAL TRANSACTIONS USING MACHINE LEARNING

## ABSTRACT
Financial fraud detection models often report artificially high F1-scores by evaluating on post-transaction features unavailable during real-time pre-authorization. This paper introduces FRAUDSENSE AI, a robust prototype enforcing strict schema-level data leakage prevention. To mitigate the friction of binary ML classification, we propose an operational APPROVE/VERIFY/BLOCK decision routing framework, bridging the gap between raw ML probabilities and business friction, alongside an explicit cold-start handler for sparse behavioral datasets. The system is fully containerized with integrated model drift tracking and case management. Complete temporal-split experiments comparing alternative machine learning models remain pending, but the foundational architecture provides a rigorous framework for deployment-oriented fraud detection research.

## KEYWORDS
Fraud Detection, Machine Learning, Data Leakage, MLOps, Pre-Authorization, XGBoost, PaySim

---

## I. INTRODUCTION
The rapid expansion of real-time digital financial transactions has necessitated the development of automated fraud detection systems [1]. However, academic research in this domain often relies on synthetic datasets where models are inadvertently trained on post-transaction states, causing severe temporal data leakage [3]. Furthermore, operational banking environments cannot rely purely on binary classification, as false positives introduce severe customer friction [5]. This paper presents FRAUDSENSE AI, a system designed to address these gaps through strict pre-authorization architectural constraints and a context-aware tri-state decision engine. 

## II. RELATED WORK
Research extensively covers machine learning applications in fraud detection, particularly utilizing the PaySim dataset [2]. However, significant gaps remain regarding MLOps integration [7], behavioral cold-start handling [6], and the mitigation of data leakage in real-time streaming contexts. *(Note: Extensive literature review pending verification).*

## III. PROBLEM STATEMENT AND RESEARCH GAP
Existing fraud detection evaluations often prioritize classification accuracy while ignoring operational constraints. Specifically, real-time payment authorization requires:
- Strict prevention of post-transaction variables from entering the inference pipeline.
- Risk-based decision routing that allows "uncertain" transactions to be challenged rather than blindly blocked.
- Safe handling of users with no prior transaction history.
This project bridges the gap between theoretical model accuracy and operational banking requirements.

## IV. PROPOSED FRAUDSENSE AI SYSTEM

### A. Dataset and Experimental Constraints
The system utilizes the PaySim dataset, heavily filtered to focus on `TRANSFER` and `CASH_OUT` events. PaySim is highly synthetic and severely imbalanced; it does not directly map to the topologies of real-world credit card or UPI networks.

### B. Leakage-Aware Pre-Authorization Validation
Features such as `newbalanceOrig` represent post-transaction states. FRAUDSENSE AI utilizes Pydantic schema validation at the API entry point to explicitly strip these variables, ensuring the model only computes risk based on strictly available pre-authorization data.

### C. Machine Learning Pipeline
The prototype currently utilizes an XGBoost baseline trained on a random split, compensating for class imbalance via `scale_pos_weight`. *(Note: Rigorous temporal-split experiments comparing Logistic Regression and Random Forest are pending execution).*

### D. Behavioral Risk Analysis
PaySim data exhibits extreme sparsity (99.85% of senders transact only once). To prevent the system from hallucinating risk on new accounts, a `BehavioralEngine` explicitly tags histories as `NONE`, `LIMITED`, or `SUFFICIENT`.

### E. Context-Aware Decision Engine
The system moves beyond binary classification by fusing ML probabilities with behavioral context. Transactions are routed to:
- **APPROVE**: Low risk.
- **VERIFY**: Medium risk (Simulated step-up authentication / OTP).
- **BLOCK**: High risk.

### F. Fraud Alert and Case Management
Blocked and Verified transactions automatically generate deduplicated cases in a SQLite-backed queue for analyst review.

### G. Model Monitoring and Drift Detection
An asynchronous task calculates the Population Stability Index (PSI) to track feature drift without impacting inference latency. Delayed analyst resolutions are used to compute live precision.

## V. EXPERIMENTAL SETUP
*Pending execution. This section will document the temporal dataset split, hyperparameters for Logistic Regression/Random Forest, and threshold optimization methodology once Step 8 is run.*

## VI. RESULTS AND DISCUSSION
Initial architectural simulations validate that the Pydantic air-gap successfully prevents post-transaction leakage. Performance testing confirms the API sustains ~118 requests/second with sub-20ms latency on a local SQLite instance. However, rigorous comparative model performance (Precision, Recall, PR-AUC) across various threshold parameters requires further experimental execution. 

## VII. LIMITATIONS AND THREATS TO VALIDITY
- **Synthetic Data**: PaySim does not represent actual UPI, credit card, or net banking channels.
- **Behavioral Sparsity**: The extreme lack of repeat transactions in PaySim severely limits empirical validation of the behavioral engine.
- **Missing Experiments**: Comparative model analysis and temporal dataset splits have not yet been executed.
- **Infrastructure**: SQLite file-locking prevents true banking-grade scalability.
- **Simulated Verification**: The step-up OTP authentication flow is simulated and lacks live customer interaction metrics.

## VIII. CONCLUSION AND FUTURE WORK
FRAUDSENSE AI provides a robust architectural template for real-time, leakage-proof fraud detection. By shifting the focus from pure classification to operational workflow (APPROVE/VERIFY/BLOCK), it reduces business friction. Future work must focus on executing rigorous temporal-split model comparisons and validating the architecture on real-world, highly dense financial datasets.

## REFERENCES
*[See REFERENCES_REQUIRING_VERIFICATION.md]*
