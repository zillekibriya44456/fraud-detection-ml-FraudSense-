# Data Quality Report: PaySim Mobile Money

**Dataset**: `dataset/PS_20174392719_1491204439457_log.csv`
**Domain**: Mobile Money / PaySim
**Target Column**: `isFraud`

## 1. Summary Statistics
- **Total Records**: 6,362,620
- **Total Columns**: 11
- **Missing Values**: 0
- **Fraudulent Transactions**: 8,213 (0.129%)
- **Legitimate Transactions**: 6,354,407 (99.871%)
- **Class Imbalance**: 1 : 773

## 2. Key Insight
> Fraud occurs **exclusively** in `TRANSFER` and `CASH_OUT` transactions.
> PAYMENT, CASH_IN, and DEBIT transactions have **zero** fraud cases.
> Training is performed on the filtered TRANSFER+CASH_OUT subset.

| Fraud by Type | Count |
|---|---|
| CASH_OUT | 4,116 |
| TRANSFER | 4,097 |
