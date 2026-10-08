# Data Leakage Audit Report: URL Phishing (PhiUSIIL)

**Dataset**: `PhiUSIIL_Phishing_URL_Dataset.csv`  
**Target**: `label`  

## 1. Feature Assessment & Leakage Classification

| Column Name | Classification | Rationale | Action |
| :--- | :--- | :--- | :--- |
| `FILENAME` | **DEFINITE_LEAKAGE** | Unique arbitrary file hash/ID. Causes memorization. | **DROPPED** |
| `URL` | **POTENTIAL_LEAKAGE** | Raw URL string. High cardinality leads to URL memorization rather than learning lexical patterns. | **DROPPED FOR TABULAR MODEL** |
| `Domain` | **POTENTIAL_LEAKAGE** | Raw domain string. High cardinality. | **DROPPED** |
| `TLD` | **SAFE_CATEGORICAL** | TLD string. Dropped in favor of numeric `TLDLength` and `TLDLegitimateProb`. | **DROPPED** |
| `Title` | **POTENTIAL_LEAKAGE** | Unstructured webpage title text. | **DROPPED** |
| URL Duplicates (425) | **POTENTIAL_LEAKAGE** | Overlapping URLs crossing train/test splits. | **DEDUPLICATED BEFORE SPLITTING** |
| 50 Numerical Features | **SAFE** | Robust structural, lexical, and DOM features. | **RETAINED & SCALED** |

## 2. Leakage Prevention Protocol
- Deduplication applied on URL strings (425 removed).
- Stratified 70/15/15 train/val/test split.
- Standard scaler fit exclusively on training data.
