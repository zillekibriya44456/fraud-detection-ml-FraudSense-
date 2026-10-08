# Data Leakage Audit Report: SMS Spam Collection

**Dataset**: `SMSSpamCollection`  
**Target**: `target` (0 = Legitimate Ham, 1 = Fraud/Spam)  

## 1. Feature Assessment & Leakage Classification

| Feature Component | Classification | Rationale | Action |
| :--- | :--- | :--- | :--- |
| Duplicate Messages (403) | **POTENTIAL_LEAKAGE** | Common spam templates duplicated across dataset could span train and test sets. | **DEDUPLICATED BEFORE SPLITTING** |
| Sender / Carrier Headers | **N/A** | Dataset contains pure message text, free of phone numbers or sender IP leaks. | **SAFE** |
| Raw Text | **SAFE** | Vectorized strictly using TF-IDF fitted on training partition. | **RETAINED** |
| Structural NLP Meta-features | **SAFE** | Computable at runtime on raw message text. | **RETAINED & SCALED** |

## 2. Leakage Prevention Protocol
- Deduplication applied on raw text strings (403 removed).
- Stratified 70/15/15 train/val/test split.
- TF-IDF vocabulary and Scaler fitted exclusively on training set.
