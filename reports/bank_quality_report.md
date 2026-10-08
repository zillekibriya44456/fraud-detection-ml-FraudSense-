# Data Quality Report: Bank Account Fraud Detection

**Dataset**: `dataset/Bank transactions/Base.csv`
**Domain**: Bank Account Fraud
**Target Column**: `fraud_bool`

## 1. Summary Statistics
- **Total Records**: 1,000,000
- **Total Columns**: 32
- **Missing Values**: 0
- **Duplicate Records**: 0
- **Legitimate Transactions**: 988,971 (98.90%)
- **Fraudulent Transactions**: 11,029 (1.10%)
- **Class Imbalance Ratio**: 1 : 89

## 2. Feature Schema
| Column Name | Data Type | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- |
| `fraud_bool` | int64 | 2 | 0 |
| `income` | float64 | 9 | 0.3 |
| `name_email_similarity` | float64 | 998861 | 0.986506310633034 |
| `prev_address_months_count` | int64 | 374 | -1 |
| `current_address_months_count` | int64 | 423 | 25 |
| `customer_age` | int64 | 9 | 40 |
| `days_since_request` | float64 | 989330 | 0.0067353870811739 |
| `intended_balcon_amount` | float64 | 994971 | 102.45371092469456 |
| `payment_type` | object | 5 | AA |
| `zip_count_4w` | int64 | 6306 | 1059 |
| `velocity_6h` | float64 | 998687 | 13096.035018400871 |
| `velocity_24h` | float64 | 998940 | 7850.955007125409 |
| `velocity_4w` | float64 | 998318 | 6742.080561007602 |
| `bank_branch_count_8w` | int64 | 2326 | 5 |
| `date_of_birth_distinct_emails_4w` | int64 | 40 | 5 |
| `employment_status` | object | 7 | CB |
| `credit_risk_score` | int64 | 551 | 163 |
| `email_is_free` | int64 | 2 | 1 |
| `housing_status` | object | 7 | BC |
| `phone_home_valid` | int64 | 2 | 0 |
| `phone_mobile_valid` | int64 | 2 | 1 |
| `bank_months_count` | int64 | 33 | 9 |
| `has_other_cards` | int64 | 2 | 0 |
| `proposed_credit_limit` | float64 | 12 | 1500.0 |
| `foreign_request` | int64 | 2 | 0 |
| `source` | object | 2 | INTERNET |
| `session_length_in_minutes` | float64 | 994887 | 16.224843433978073 |
| `device_os` | object | 5 | linux |
| `keep_alive_session` | int64 | 2 | 1 |
| `device_distinct_emails_8w` | int64 | 4 | 1 |
| `device_fraud_count` | int64 | 1 | 0 |
| `month` | int64 | 8 | 0 |
