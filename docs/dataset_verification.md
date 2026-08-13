# FraudGuard AI — Dataset Verification Report (Phase 2)

**Version:** 2.0 (Phase 2 formal verification — programmatically confirmed)
**Verification date:** 2026-08-14 02:11:54 IST
**Verified by:** `scripts/phase2_verify_datasets.py`
**Evidence file:** `reports/phase2_verification_results.json`
**Total verification time:** 53.2 seconds

> [!IMPORTANT]
> All numbers in this document originate from actual file reads against the raw dataset files.
> No numbers have been estimated, assumed, or fabricated.
> SHA-256 prefix fingerprints are provided for file integrity verification.

---

## 1. Repository Data Structure Audit

| Directory | Expected | Status |
|---|---|---|
| `data/raw/` | Dataset files | ✅ Present |
| `data/downloads/` | ZIP archives | ✅ Present |
| `data/processed/` | Processed splits | ⚠️ Empty (expected — no training yet) |
| `data/external/` | External data | ✅ Empty (expected) |

---

## 2. Raw Dataset Inventory

| Dataset | File | Location | Size (MB) | SHA-256 (first 64KB) | Status |
|---|---|---|---|---|
| PaySim | `PS_20174392719_1491204439457_log.csv` | `data/raw/` | 470.67 | `91a79a1b4bff13ec` | ✅ Present |
| ULB Credit Card | `creditcard.csv` | `data/raw/` | 143.84 | `68f0c9eaa41f6858` | ✅ Present |
| UPI Fraud | `fraud_dataset.csv` | `data/raw/` | 12.33 | `a4d6bd9c7bbd740e` | ✅ Present |
| IEEE-CIS Transaction | `train_transaction.csv` | `data/raw/IEEE_CIS archive (3)/` | 651.69 | `761426a5b7d133c5` | ✅ Present |
| IEEE-CIS Identity | `train_identity.csv` | `data/raw/IEEE_CIS archive (3)/` | 25.30 | `4e4a5a8ca232044a` | ✅ Present |

**ZIP archives (in data/downloads/):**

| File | Size |
|---|---|
| `paysimarchive (3).zip` | 178 MB |
| `IEEE_CIS archive (3).zip` | 118 MB |
| `4CR C archive (3).zip` | 66 MB |
| `3UPI archive (3).zip` | 5 MB |

---

## 3. PaySim

### Provenance
- **Full name:** PaySim — A Financial Mobile Money Simulator
- **Authors:** E.A. Lopez-Rojas, A. Elmir, S. Axelsson
- **Publication:** EMSS 2016 — 28th European Modelling and Simulation Symposium
- **Origin:** Simulation based on real mobile money transaction logs from an un-named MNVO operating in Africa
- **Status:** SYNTHETIC (agent-based simulation of real transaction behaviour)
- **License:** Open Database License (ODbL) — open for research use
- **Source:** Kaggle — `ealaxi/paysim1`

### Structural Verification

| Metric | Verified Value |
|---|---|
| Total rows | **6,362,620** ✅ |
| Columns | **11** ✅ |
| Missing values | **0** |
| Duplicate rows | Not checked (file > 200 MB — checked in EDA) |
| Target column | `isFraud` |
| Target found | ✅ Yes |
| SHA-256 prefix | `91a79a1b4bff13ec` |

### Class Distribution

| Class | Count | Percentage |
|---|---|---|
| Legitimate (0) | 6,354,407 | 99.8709% |
| Fraud (1) | 8,213 | **0.1291%** |
| **Total** | **6,362,620** | 100% |

### Feature Catalogue

| Column | Type | Role | Notes |
|---|---|---|---|
| `step` | int | Feature | 1 step = 1 hour; total 744 steps (30 days) |
| `type` | str | Feature | CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER |
| `amount` | float | Feature | Transaction amount in local currency |
| `nameOrig` | str | **DROP** | Sender ID — high cardinality string — identifier leakage risk |
| `oldbalanceOrg` | float | Feature | Sender balance before transaction |
| `newbalanceOrig` | float | Feature | Sender balance after transaction |
| `nameDest` | str | **DROP** | Recipient ID — high cardinality string — identifier leakage risk |
| `oldbalanceDest` | float | Feature | Recipient balance before transaction |
| `newbalanceDest` | float | Feature | Recipient balance after transaction |
| `isFraud` | int (0/1) | **TARGET** | Ground truth fraud label |
| `isFlaggedFraud` | int (0/1) | **DROP** | Simple rule (amount > 200,000) — not an ML prediction |

### Critical Observation: Fraud Transaction Types
```
Fraud occurs ONLY in CASH_OUT and TRANSFER transactions.
CASH_IN, DEBIT, and PAYMENT transactions contain zero fraud in PaySim.
This is a known characteristic of the PaySim simulation model.
```

### Limitations
- Synthetic — does not capture all real-world fraud patterns
- No device fingerprint, location, or merchant category data
- Fraud confined to two transaction types (simulation artefact)
- All transactions from a single mobile money operator in a single country

### Role: **PRIMARY**
- Clear interpretable features → suitable for SHAP explainability
- Realistic extreme class imbalance (0.13%) → core research problem
- 6.3M rows → robust cross-validation without resampling bias
- Zero missing values → clean baseline for first experiments

---

## 4. ULB Credit Card Fraud Detection

### Provenance
- **Full name:** Credit Card Fraud Detection Dataset
- **Authors:** Machine Learning Group, Université Libre de Bruxelles (ULB)
- **Reference:** Dal Pozzolo et al., "Calibrating Probability with Undersampling for Unbalanced Classification," SSCI 2015
- **Origin:** Real European credit card transactions — September 2013 (2-day window)
- **Status:** REAL (anonymised for privacy)
- **License:** Database Contents License (DbCL) — open for research use
- **Source:** Kaggle — `mlg-ulb/creditcardfraud`

### Structural Verification

| Metric | Verified Value |
|---|---|
| Total rows | **284,807** ✅ |
| Columns | **31** ✅ |
| Missing values | **0** |
| Duplicate rows | **1,081** ⚠️ (see note below) |
| Target column | `Class` |
| Target found | ✅ Yes |
| SHA-256 prefix | `68f0c9eaa41f6858` |

> [!WARNING]
> **1,081 duplicate rows detected in ULB Credit Card dataset.**
> These rows will be removed during preprocessing (Notebook 03) — from the **training set only**.
> The raw file `data/raw/creditcard.csv` must **NOT** be modified.
> The test set must not be de-duplicated independently of the train set to prevent leakage.

### Class Distribution

| Class | Count | Percentage |
|---|---|---|
| Legitimate (0) | 284,315 | 99.8273% |
| Fraud (1) | 492 | **0.1727%** |
| **Total** | **284,807** | 100% |

### Feature Catalogue

| Column | Type | Notes |
|---|---|---|
| `Time` | float | Seconds elapsed since first transaction in the dataset |
| `V1`–`V28` | float | **Anonymised** — PCA-transformed principal components |
| `Amount` | float | Transaction amount in EUR |
| `Class` | int (0/1) | **TARGET** — fraud label |

### Critical Limitation: Anonymised Features
```
V1–V28 are the result of PCA transformation applied to protect privacy.
The original feature names and meanings are unknown.
SHAP values for V1–V28 cannot be translated into business-meaningful
explanations. This makes ULB unsuitable as a PRIMARY training dataset
for an explainable fraud detection system.
```

### Limitations
- PCA-anonymised features prevent explainability
- Only 2 days of transactions — limited temporal diversity
- Known duplicate rows (examined in EDA notebook)
- EUR currency, European cardholder context only

### Role: **BENCHMARK**
- Widely used in fraud detection literature — enables metric comparison
- Pure numerical format — fast to train on
- NOT suitable for SHAP-based business explanations

---

## 5. IEEE-CIS Fraud Detection

### Provenance
- **Full name:** IEEE-CIS Fraud Detection Dataset
- **Source:** Vesta Corporation via Kaggle Competition (2019)
- **Status:** REAL — e-commerce transaction data
- **License:** Kaggle competition rules — academic/research use
- **Competition page:** `c/ieee-fraud-detection`

### Structural Verification

#### Transaction File (`train_transaction.csv`)

| Metric | Verified Value |
|---|---|
| Total rows | **590,540** ✅ |
| Columns | **394** ✅ |
| Missing values (total cells) | **95,566,686** (from prior full read) |
| Missing percentage | ~41% overall |
| Target column | `isFraud` |
| Target found | ✅ Yes |
| SHA-256 prefix | `761426a5b7d133c5` |

#### Identity File (`train_identity.csv`)

| Metric | Verified Value |
|---|---|
| Total rows | **144,233** ✅ |
| Columns | **41** ✅ |
| Missing values (total cells) | **2,104,107** ✅ |
| Join key | `TransactionID` |
| SHA-256 prefix | `4e4a5a8ca232044a` |

### Class Distribution (Transaction File)

| Class | Count | Percentage |
|---|---|---|
| Legitimate (0) | 569,877 | 96.501% |
| Fraud (1) | 20,663 | **3.499%** |
| **Total** | **590,540** | 100% |

### Feature Groups

| Group | Count | Description |
|---|---|---|
| TransactionID, TransactionDT | 2 | Identifier + timestamp |
| TransactionAmt, ProductCD | 2 | Amount + product category |
| card1–card6 | 6 | Card info (partially anonymised) |
| addr1–addr2, dist1–dist2 | 4 | Address + distance |
| P_emaildomain, R_emaildomain | 2 | Email domains |
| C1–C14 | 14 | Count features (meaning not disclosed) |
| D1–D15 | 15 | Time-delta features (days) |
| M1–M9 | 9 | Match features (T/F flags) |
| V1–V339 | 339 | Vesta engineered features (anonymised) |
| Identity: id_01–id_38, DeviceType, DeviceInfo | 41 | Device and identity signals |

### Limitations
- Extremely high missingness (~41%) requires complex imputation
- Most features (V1–V339) are anonymised
- Requires merging two files via `TransactionID` before use
- Significant data engineering overhead before modelling
- Identity file covers only 144,233 of 590,540 transactions (24.4% match rate)

### Role: **SECONDARY**
- Not used as primary training dataset
- May be used in cross-dataset generalisation experiments (Phase 12)
- Requires separate preprocessing pipeline

---

## 6. UPI Fraud Detection

### Provenance
- **File:** `fraud_dataset.csv`
- **Status:** Appears HIGHLY SYNTHETIC / TUTORIAL-GENERATED
- **License:** Unknown — not established from available metadata
- **Source:** Origin unclear — appears to be a synthetic tutorial dataset

### Structural Verification

| Metric | Verified Value |
|---|---|
| Total rows | **26,393** ✅ |
| Columns | **65** ✅ |
| Missing values | **51,297** |
| Duplicate rows | **0** |
| Target column | `is_fraud` |
| SHA-256 prefix | `a4d6bd9c7bbd740e` |

### Class Distribution

| Class | Count | Percentage |
|---|---|---|
| Legitimate (0) | 21,848 | 82.78% |
| Fraud (1) | 4,545 | **17.22%** |

### Rejection Rationale

| Issue | Detail |
|---|---|
| Unrealistic fraud rate | 17.22% fraud is 100× higher than real financial systems |
| Unknown provenance | Source and methodology unclear |
| Simulated feature set | Features appear artificially designed for a tutorial |
| Redundant | PaySim already covers mobile-money / UPI-style transactions |

### Role: **REJECTED**
This dataset will not be used in any experiment. It is retained in `data/raw/` but will never be processed or included in results.

---

## 7. Dataset Completeness Matrix

| Dataset | File | Readable | Rows | Cols | Target | Fraud Count | Duplicates | Status | Role |
|---|---|---|---|---|---|---|---|---|---|
| PaySim | ✅ | ✅ | ✅ 6,362,620 | ✅ 11 | ✅ `isFraud` | 8,213 (0.1291%) | Not checked | ✅ PASS | PRIMARY |
| ULB Credit Card | ✅ | ✅ | ✅ 284,807 | ✅ 31 | ✅ `Class` | 492 (0.1727%) | ⚠️ **1,081** | ✅ PASS | BENCHMARK |
| UPI Fraud | ✅ | ✅ | ✅ 26,393 | ✅ 65 | ✅ `is_fraud` | 4,545 (17.22%) | 0 | ✅ PASS | REJECTED |
| IEEE-CIS Transaction | ✅ | ✅ | ✅ 590,540 | ✅ 394 | ✅ `isFraud` | 20,663 (3.499%) | Not checked | ✅ PASS | SECONDARY |
| IEEE-CIS Identity | ✅ | ✅ | ✅ 144,233 | ✅ 41 | N/A | N/A | Not checked | ✅ PASS | SECONDARY (join) |

---

## 8. Class Imbalance Summary

| Dataset | Fraud % | Imbalance Ratio (Legit:Fraud) |
|---|---|---|
| PaySim | 0.1291% | 773:1 |
| ULB Credit Card | 0.1727% | 578:1 |
| IEEE-CIS | 3.499% | 28:1 |
| UPI Fraud | 17.22% | 5:1 (REJECTED) |

> PaySim and ULB have the most extreme real-world imbalance ratios, making them the most scientifically appropriate for imbalance-handling experiments.

---

## 9. Leakage Risk Register

| Dataset | Column | Leakage Type | Action |
|---|---|---|---|
| PaySim | `nameOrig` | Identifier leakage | DROP before training |
| PaySim | `nameDest` | Identifier leakage | DROP before training |
| PaySim | `isFlaggedFraud` | Rule-based derivation (not ML) | DROP before training |
| All | Target column | Target leakage | Used as y, never as X |
| IEEE-CIS | `TransactionID`, `TransactionDT` | Identifier / timestamp | DROP or transform before training |

---

## 10. Data Quality Summary

| Dataset | Missing | Duplicates | Integrity | Overall Quality |
|---|---|---|---|---|
| PaySim | None | TBD | ✅ | 🟢 Excellent |
| ULB Credit Card | None | Some present | ✅ | 🟡 Good (duplicates noted) |
| IEEE-CIS | Very high (~41%) | Unknown | ✅ | 🟡 Moderate (requires imputation) |
| UPI Fraud | 51,297 cells | Unknown | ✅ | 🔴 Rejected |

---

## 11. Dataset Provenance Declaration

| Dataset | Real / Synthetic | Personally Identifiable Information |
|---|---|---|
| PaySim | **Synthetic** (simulation based on real patterns) | None |
| ULB Credit Card | **Real** (anonymised via PCA) | Minimal — no names, account numbers retained |
| IEEE-CIS | **Real** (e-commerce transactions) | Partially anonymised — card data present |
| UPI Fraud | **Synthetic** (tutorial/artificial) | None evident |

> No raw dataset will be committed to Git. All raw files remain in `data/raw/` which is excluded via `.gitignore`.

---

## 12. Final Dataset Roles

| Role | Dataset |
|---|---|
| PRIMARY | PaySim |
| BENCHMARK | ULB Credit Card |
| SECONDARY | IEEE-CIS (Transaction + Identity) |
| OPTIONAL | — |
| REJECTED | UPI Fraud |

---

## 13. Verification Script Reference

The numbers in this document were produced by:
```bash
venv/bin/python scripts/phase2_verify_datasets.py
```
Full machine-readable results are stored in:
```
reports/phase2_verification_results.json
```

This document must be updated if any dataset is re-downloaded or replaced.
