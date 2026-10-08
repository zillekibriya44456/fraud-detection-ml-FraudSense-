# Data Leakage Audit Report: Credit Card Fraud

**Dataset**: `creditcard.csv`  
**Target**: `Class`  

## 1. Feature Assessment & Leakage Classification

| Column Name | Classification | Rationale | Action |
| :--- | :--- | :--- | :--- |
| `Class` | **TARGET** | Ground truth label. | Target variable. |
| Duplicate rows (1,081) | **POTENTIAL_LEAKAGE** | Identical transaction records could leak across train and test partitions. | **DEDUPLICATED BEFORE SPLITTING** |
| `V1` – `V28` | **SAFE** | Numerical PCA features available at transaction time. | **RETAINED** |
| `Amount` | **SAFE** | Real-time transaction amount. | **SCALED WITH ROBUSTSCALER** |
| `Time` | **SAFE_WITH_EXTRACTION** | Raw elapsed seconds. Transformed into cyclical `hour_of_day` and `is_night`. | **ENGINEERED & RETAINED** |

## 2. Leakage Prevention Protocol
- Deduplication applied (1,081 rows removed).
- 70/15/15 stratified train/val/test split executed prior to scaler fitting.
- Scaler fit solely on training data.
