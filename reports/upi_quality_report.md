# Data Quality Report: UPI Transactions 2024

**Dataset**: `dataset/upi_transactions_2024.csv`
**Domain**: UPI (Unified Payments Interface)
**Target Column**: `fraud_flag`

> [!WARNING]
> Statistical analysis reveals **near-zero correlation** between all available features and fraud labels
> (max point-biserial r=0.0044; all chi-squared p > 0.05). The fraud labels in this synthetic
> dataset appear quasi-randomly assigned, which fundamentally limits achievable model discrimination.

## 1. Summary Statistics
- **Total Records**: 250,000
- **Total Columns**: 17
- **Missing Values**: 0 (0.00%)
- **Duplicate Records**: 0 (0.00%)
- **Legitimate Transactions**: 249,520 (99.81%)
- **Fraudulent Transactions**: 480 (0.192%)
- **Class Imbalance Ratio**: 1 : 519

## 2. Feature Schema & Types
| Column Name | Data Type | Missing Count | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- | :--- |
| `transaction id` | object | 0 | 250000 | TXN0000000001 |
| `timestamp` | object | 0 | 248610 | 2024-10-08 15:17:28 |
| `transaction type` | object | 0 | 4 | P2P |
| `merchant_category` | object | 0 | 10 | Entertainment |
| `amount (INR)` | int64 | 0 | 10355 | 868 |
| `transaction_status` | object | 0 | 2 | SUCCESS |
| `sender_age_group` | object | 0 | 5 | 26-35 |
| `receiver_age_group` | object | 0 | 5 | 18-25 |
| `sender_state` | object | 0 | 10 | Delhi |
| `sender_bank` | object | 0 | 8 | Axis |
| `receiver_bank` | object | 0 | 8 | SBI |
| `device_type` | object | 0 | 3 | Android |
| `network_type` | object | 0 | 4 | 4G |
| `fraud_flag` | int64 | 0 | 2 | 0 |
| `hour_of_day` | int64 | 0 | 24 | 15 |
| `day_of_week` | object | 0 | 7 | Tuesday |
| `is_weekend` | int64 | 0 | 2 | 0 |
