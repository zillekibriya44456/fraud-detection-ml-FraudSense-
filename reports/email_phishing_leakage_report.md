# Data Leakage Audit Report: Email Phishing

**Dataset**: `phishing_email.csv`  
**Target**: `label` (0 = Legitimate, 1 = Phishing)  

## 1. Feature Assessment & Leakage Classification

| Feature Component | Classification | Rationale | Action |
| :--- | :--- | :--- | :--- |
| Duplicate Emails (408) | **POTENTIAL_LEAKAGE** | Identical spam campaigns could cross-contaminate train and test splits. | **DEDUPLICATED BEFORE SPLITTING** |
| Header Metadata | **N/A** | Text corpus consists of body and subject text (`text_combined`), preventing IP or routing header leaks. | **SAFE** |
| Raw Text | **SAFE** | Vectorized using TF-IDF fitted strictly on training data. | **RETAINED** |
| Structural NLP Meta-features | **SAFE** | Real-time computable structural signals (urgency, credentials, financial terms, URLs). | **RETAINED & SCALED** |

## 2. Leakage Prevention Protocol
- Deduplication applied on raw email text strings (408 removed).
- Stratified 70/15/15 train/val/test split.
- TF-IDF vocabulary (top 4,000 terms) and Scaler fitted exclusively on training set.
