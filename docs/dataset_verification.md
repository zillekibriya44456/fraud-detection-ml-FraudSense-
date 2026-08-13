# FraudGuard AI — Dataset Verification Report

## 1. Verification Date
August 9, 2026

## 2. Repository Data Structure
- `data/downloads/`: Empty / not populated.
- `data/raw/`: Contains the actual dataset files (`creditcard.csv`, `fraud_dataset.csv`, `PS_20174392719_1491204439457_log.csv`, and `IEEE_CIS archive (3)` folder).
- `data/processed/`: Empty (as expected in Phase 2A).

## 3. Dataset Inventory
1. **IEEE-CIS Fraud Detection**: Extracted folder (`IEEE_CIS archive (3)`) containing transaction and identity data.
2. **PaySim**: Single CSV file (`PS_20174392719_1491204439457_log.csv`).
3. **UPI Fraud Detection**: Single CSV file (`fraud_dataset.csv`).
4. **ULB Credit Card Fraud Detection**: Single CSV file (`creditcard.csv`).

## 4. IEEE-CIS Verification
- **Transaction File**: `train_transaction.csv`
  - Rows: 590,540 | Columns: 394
  - Missing Values: 95,566,686 (Very high missingness, ~41% overall)
  - Target Location: `isFraud` column found.
- **Identity File**: `train_identity.csv`
  - Rows: 144,233 | Columns: 41
  - Missing Values: 2,104,107
- **Connection**: Files can be joined via `TransactionID` in the future.

## 5. PaySim Verification
- **File**: `PS_20174392719_1491204439457_log.csv`
- **Rows**: 6,362,620 | Columns: 11
- **Missing Values**: 0
- **Features Found**: 
  - Transaction Type (`type`)
  - Amount (`amount`)
  - Sender Info (`nameOrig`, `oldbalanceOrg`, `newbalanceOrig`)
  - Receiver Info (`nameDest`, `oldbalanceDest`, `newbalanceDest`)
  - Fraud Label (`isFraud`)
- **Status**: Excellent structural integrity.

## 6. UPI Verification
- **File**: `fraud_dataset.csv`
- **Rows**: 26,393 | Columns: 65
- **Missing Values**: 51,297
- **Features Found**: Extensive synthetic behavioral flags (e.g. `unusual_device_flag`, `otp_request_frequency`, `time_to_respond_to_request`, `authentication_attempts`).
- **Fraud Label**: `is_fraud`

## 7. ULB Verification
- **File**: `creditcard.csv`
- **Rows**: 284,807 | Columns: 31
- **Missing Values**: 0
- **Features Found**: `Time`, `Amount`, and V1-V28 (anonymized/PCA).
- **Fraud Label**: `Class`

## 8. Dataset Completeness
| Dataset | Downloaded | Extracted | Readable | Complete | Target Found | Fraud Labels | Status |
|---|---|---|---|---|---|---|---|
| PaySim | Yes | Yes | Yes | Yes | Yes | `isFraud` | GREEN |
| ULB Credit Card | Yes | Yes | Yes | Yes | Yes | `Class` | GREEN |
| UPI Fraud | Yes | Yes | Yes | Yes | Yes | `is_fraud` | GREEN |
| IEEE-CIS | Yes | Yes | Yes | Yes | Yes | `isFraud` | YELLOW (Requires complex joining and heavy missing-value imputation) |

## 9. Class Distribution
| Dataset | Legitimate | Fraud | Total | Fraud % |
|---|---|---|---|---|
| ULB Credit Card | 284,315 | 492 | 284,807 | 0.1727% |
| PaySim | 6,354,407 | 8,213 | 6,362,620 | 0.1291% |
| UPI Fraud | 21,848 | 4,545 | 26,393 | 17.22% |
| IEEE-CIS Transaction | 569,877 | 20,663 | 590,540 | 3.499% |

## 10. Data Quality
- **PaySim**: Perfect structural quality. Zero missing values. Immense dataset (6.3M rows) with a realistic extreme imbalance (0.13% fraud).
- **ULB**: Perfect structural quality. Zero missing values. Pure numerical format. Extreme imbalance (0.17% fraud). No business/behavioral feature names.
- **UPI**: High missing values (51K total). Extremely high, arguably unrealistic fraud rate (17.22%) for standard banking traffic, heavily suggesting it is simulated/synthetic.
- **IEEE-CIS**: Massive missing values (95 Million total in transaction file). High cardinality. Highly complex.

## 11. Dataset Suitability
1. **PaySim**: Highly suitable. Contains clear financial features (balances, amounts) necessary for behavioral engineering and transparent Explainable AI. Size (6.3M) supports robust train/test splits.
2. **ULB Credit Card**: Useful benchmark for anomaly detection algorithms, but anonymized features (V1-V28) make it useless for Explainable AI (you can't explain to a user why "V4" is high).
3. **UPI Fraud**: Contains overly specific features that seem artificially generated for a specific tutorial, and the 17% fraud rate is non-representative of real finance systems. 
4. **IEEE-CIS**: Extremely feature-rich but requires massive data engineering just to prepare, risking distracting from the core goals of building a real-time risk engine and API architecture.

## 12. Dataset Limitations
- **PaySim**: Synthetic dataset. Does not contain raw merchant categories or device fingerprints.
- **ULB Credit Card**: Anonymized features block explainability.
- **UPI Fraud**: Unrealistic class imbalance and highly simulated feature set.
- **IEEE-CIS**: Extremely noisy, high missingness, anonymized identity features.

## 13. Data Provenance
- **PaySim**: Synthetic dataset based on real mobile money transactions (E.A. Lopez-Rojas). 
- **ULB**: Real credit card transactions from European cardholders in September 2013, highly PCA transformed.
- **UPI Fraud**: Not established from local files (appears highly synthetic/tutorial-oriented).
- **IEEE-CIS**: Provided by Vesta Corporation for a Kaggle competition. Real-world e-commerce data.

## 14. Final Recommendation
- **PRIMARY:** PaySim
- **BENCHMARK:** ULB Credit Card Fraud
- **OPTIONAL / SECONDARY:** IEEE-CIS
- **REJECT:** UPI Fraud
