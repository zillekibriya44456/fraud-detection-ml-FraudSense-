# Data Leakage Audit: Elliptic Bitcoin Dataset

**Dataset**: `elliptic_txs_features.csv`
**Target**: `fraud_flag`

## Feature Assessment
- The dataset contains 166 anonymized numerical features.
- First 94 features are local information (transaction inputs/outputs, fee, size, etc.).
- Remaining 72 features are aggregated network information from 1-hop backward/forward neighbors.
- `txId` is dropped to prevent memorization.
- `time_step` (1 to 49) represents ~2 weeks of transactions each.

## Leakage Prevention Protocol
- **Temporal Splitting**: To avoid future leakage, data is split chronologically:
  - Train: Steps 1 to 34
  - Validation: Steps 35 to 42
  - Test: Steps 43 to 49
- Features are scaled strictly using training data statistics.
