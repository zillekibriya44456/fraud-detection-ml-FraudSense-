# Data Quality Report: Credit Card Fraud

**Dataset**: `data/raw/card/creditcard.csv`  
**Domain**: Card (Credit / Debit Card Transactions)  
**Target Column**: `Class` (0 = Legitimate, 1 = Fraud)  

## 1. Summary Statistics
- **Total Records**: 284,807
- **Total Columns**: 31
- **Missing Values**: 0 (0.00%)
- **Duplicate Records**: 1,081 (0.38%)
- **Post-Deduplication Records**: 283,726
- **Legitimate Transactions**: 284,315 (99.827%)
- **Fraudulent Transactions**: 492 (0.173%)
- **Class Imbalance Ratio**: 1 : 577

## 2. Feature Schema & Types
- **`Time`**: Elapsed seconds since first recorded transaction in dataset (spanning 48 hours).
- **`V1` – `V28`**: PCA transformed numerical components from original card features (confidentiality transformation).
- **`Amount`**: Transaction dollar amount.
- **`Class`**: Ground truth target label.
