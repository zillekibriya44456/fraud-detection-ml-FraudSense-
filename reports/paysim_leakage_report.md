# Data Leakage Audit: PaySim Mobile Money

**Dataset**: `PS_20174392719_1491204439457_log.csv`
**Target**: `isFraud`

## Feature Assessment

| Feature | Classification | Rationale | Action |
| :--- | :--- | :--- | :--- |
| `step` | SAFE | Simulated time step (1 step = 1 hour). Temporal signal. | RETAINED |
| `type` | SAFE | Transaction type (TRANSFER/CASH_OUT). Available at authorization. | RETAINED |
| `amount` | SAFE | Transaction amount. Available at authorization. | RETAINED |
| `nameOrig` | DEFINITE_LEAKAGE | Customer ID — unique entity identifier. Induces memorization. | **DROPPED** |
| `oldbalanceOrg` | SAFE | Originator balance before transaction. Available at authorization. | RETAINED |
| `newbalanceOrig` | **POTENTIAL_LEAKAGE** | Originator balance AFTER transaction. Post-event signal. Used carefully — retained as it reveals zero-drain patterns. | RETAINED with caution |
| `nameDest` | DEFINITE_LEAKAGE | Destination ID — unique entity. | **DROPPED** |
| `oldbalanceDest` | SAFE | Destination balance before transaction. Available at authorization. | RETAINED |
| `newbalanceDest` | **POTENTIAL_LEAKAGE** | Destination balance AFTER. Post-event; retained for zero-balance trap detection. | RETAINED with caution |
| `isFlaggedFraud` | **DEFINITE_LEAKAGE** | Bank's own fraud flag — computed post-decision. Only 16 flags in 6.3M rows (useless and leaky). | **DROPPED** |

## Leakage Prevention Protocol
- `nameOrig`, `nameDest`, `isFlaggedFraud` dropped before training.
- `newbalanceOrig` and `newbalanceDest` retained because they encode the key fraud pattern
  (complete drain of origin account + zero dest balance = strong signal).
- Stratified 70/15/15 split on TRANSFER+CASH_OUT filtered subset.
- Preprocessor fitted strictly on training data.
