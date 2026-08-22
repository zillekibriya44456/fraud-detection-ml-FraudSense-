# Behavioral Feature Feasibility Matrix

## Temporal Structure Analysis
The PaySim dataset contains 6,362,620 transactions.
- **Unique Senders (`nameOrig`)**: 6,353,307 (99.85% unique)
- **Unique Recipients (`nameDest`)**: 2,722,362

Because almost every sender transacts exactly once, constructing a "historical sender profile" is theoretically impossible for the vast majority of the population. They will always present as a "Cold Start".

However, recipients (merchants, transfers) receive funds multiple times.

## Feasibility Matrix

| FEATURE | DATA AVAILABLE? | CAN BE DERIVED? | REAL-TIME AVAILABLE? | FUTURE DATA LEAKAGE RISK? | IMPLEMENT NOW? | REASON |
|---|---|---|---|---|---|---|
| Transaction velocity (Sender) | No (Sparse) | Yes | Yes | No (if cached) | Yes (Architecture) | We build the engine to support it, but it will mostly return 0. |
| Transaction count in recent window | Yes (Recipients) | Yes | Yes | No (if cached) | Yes | Supported for recipients. |
| Time since previous transaction | No (Sparse) | Yes | Yes | No | Yes (Architecture) | Will return null/None for cold starts. |
| Rolling average amount | No (Sparse) | Yes | Yes | No | Yes (Architecture) | Will return current amount for cold starts. |
| Amount deviation from history | No (Sparse) | Yes | Yes | No | Yes (Architecture) | Defaults to 0 deviation on cold starts. |
| New beneficiary indicator | Yes | Yes | Yes | No | Yes | If `recipient_transaction_count == 0` for a sender, it is new. |

## Conclusion
We will build the **Behavioral Engine Architecture** to process these features safely in real-time, preventing the current transaction $T_n$ from leaking into its own calculation. However, due to data sparsity, we will **not** retrain the XGBoost model on these features, as the model will learn that default/cold-start values are the norm. Instead, the engine will generate a parallel `Behavioral Risk Signal` that fuses with the ML output.
