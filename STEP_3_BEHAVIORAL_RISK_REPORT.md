# STEP 3: BEHAVIORAL RISK AND TRANSACTION VELOCITY ENGINE REPORT

## 1. Dataset Feasibility Findings
- Analyzed 6.36 million PaySim transactions.
- **Critical Finding**: 99.85% of senders (`nameOrig`) transact exactly ONCE. 
- **Conclusion**: Sender historical velocity cannot be reliably tracked on this specific dataset on a population level without triggering a "Cold Start" for almost every transaction.

## 2. Temporal Leakage Analysis
To prevent data leakage, the architecture strictly enforces temporal boundaries:
- A transaction is evaluated using only the historical state that existed **before** it arrived.
- The transaction is injected into the historical state only **after** the prediction and behavioral assessment have completed.
- This was explicitly validated via new test cases (`test_leakage_prevention`).

## 3. Features Implemented
- `sender_transaction_count_recent`: Transaction velocity of the sender.
- `recipient_transaction_count_recent`: Frequency of recipient deposits.
- `amount_deviation_score`: Heuristic anomaly score measuring the ratio between the current transaction and the historical average.
- `is_new_recipient`: Boolean flag.
- `behavioral_risk_signal`: A scalar heuristic anomaly score bounded [0.0, 1.0].

## 4. Integration Approach
Because of the sparse nature of the dataset, it is statistically dangerous to retrain the XGBoost model on behavioral features (it would learn that `velocity=0` means safe, which is a false correlation). 

Instead, we built a **Risk Fusion Layer** in `api/services.py`:
1. ML Fraud Probability is calculated.
2. The `BehavioralEngine` calculates a parallel heuristic `behavioral_risk_signal`.
3. Both signals are returned to the API for downstream policy enforcement.

## 5. Cold-Start Strategy
Transactions from unseen accounts return `behavioral_history_status: "NONE"` and a risk signal of `0.0`. The system smoothly defaults to the XGBoost pre-authorization model, refusing to penalize users for lack of history.

## 6. Performance Measurements
- **Total Test Suite Time**: 5.57s for 12 tests (including model loading overhead).
- **Inference Latency**: The `BehavioralEngine` utilizes O(1) hash map lookups (`collections.defaultdict`), adding less than ~0.1ms to the total API response latency. It easily meets real-time prototyping requirements.

## 7. Tests Added
- `test_cold_start_transaction`: Validates graceful degradation.
- `test_leakage_prevention`: Ensures $T_n$ cannot see itself.
- `test_velocity_amount_deviation`: Validates correct heuristic score calculation when an anomalous spike occurs.

## 8. Total Test Results
- **Run**: `pytest`
- **Result**: `12 passed`
- **Status**: 100% Pass Rate.

## 9. Production Considerations
For a real-world enterprise deployment:
1. The `collections.defaultdict` in-memory tracker must be replaced with an external Redis cluster (using Sorted Sets for sliding time windows).
2. A real-world dataset will have higher density, allowing for XGBoost retraining on the behavioral output (stacking).

========================================================

**STEP 3 STATUS: PASS WITH LIMITATIONS**
*(Passed functionally and architecturally. Limited only by the sparsity of the underlying PaySim dataset).*
