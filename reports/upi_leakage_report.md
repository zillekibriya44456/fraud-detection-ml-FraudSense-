# Data Leakage Audit Report: UPI Transactions 2024

**Dataset**: `upi_transactions_2024.csv`
**Target**: `fraud_flag`

## 1. Feature Assessment & Leakage Classification

| Column Name | Classification | Rationale | Action |
| :--- | :--- | :--- | :--- |
| `transaction id` | **DEFINITE_LEAKAGE** | Unique arbitrary transaction identifier. Induces memorization. | **DROPPED** |
| `transaction_status` | **POTENTIAL_LEAKAGE** | Post-authorization outcome ('SUCCESS'/'FAILED'). Unknown at real-time scoring. | **DROPPED** |
| `timestamp` | **SAFE_WITH_EXTRACTION** | Raw datetime string. Replaced with cyclic time features. | **EXTRACTED & RAW DROPPED** |
| `amount (INR)` | **SAFE** | Real-time requested payment amount. | **RETAINED** |
| `transaction type` | **SAFE** | P2P, P2M, Bill Payment, Recharge. | **RETAINED** |
| `merchant_category` | **SAFE** | Merchant category. Available at authorization. | **RETAINED** |
| `sender_age_group` | **SAFE** | KYC demographic attribute. | **RETAINED** |
| `receiver_age_group`| **SAFE** | Counterparty profile attribute. | **RETAINED** |
| `sender_state` | **SAFE** | Originating geo/state. | **RETAINED** |
| `sender_bank` | **SAFE** | Remitter bank identifier. | **RETAINED** |
| `receiver_bank` | **SAFE** | Beneficiary bank identifier. | **RETAINED** |
| `device_type` | **SAFE** | Android, iOS, Web. Client header. | **RETAINED** |
| `network_type` | **SAFE** | 4G, 5G, WiFi, 3G. Connection protocol. | **RETAINED** |

## 2. Leakage Prevention Protocol
- Deduplication verified (0 duplicates across sets).
- Stratified 70/15/15 split created before preprocessor fitting.
- Preprocessor fitted strictly on training data.
- IsolationForest anomaly scores fitted strictly on training data.
