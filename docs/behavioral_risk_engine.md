# Behavioral Risk Engine Architecture

## 1. Purpose
The Behavioral Risk Engine tracks transaction velocity and historical patterns in real-time. It provides heuristic anomaly scores that fuse with the ML Fraud Probability model, allowing the system to detect account takeovers and sudden spending spikes.

## 2. Dataset Capability & Limitations
The current underlying data (PaySim) is highly sparse regarding sender history (99.85% of senders transact exactly once). As such, training the primary XGBoost model on behavioral features directly would cause it to learn that `velocity=0` is the default safe state. 

Therefore, the Behavioral Engine acts as a **parallel heuristic fusion layer**.

## 3. Temporal Ordering & Leakage Prevention
To prevent Data Leakage, the engine enforces strict temporal ordering:
1. `assess_transaction()`: Analyzes the current transaction using only historical state $T_0 ... T_{n-1}$.
2. `record_transaction()`: Pushes the current transaction into the history state.

This guarantees the current transaction $T_n$ never influences its own anomaly score.

## 4. Cold-Start Strategy
If a user is not found in the in-memory history tracker, the engine returns `"behavioral_history_status": "NONE"`. The system smoothly falls back to the core XGBoost prediction without penalizing the user for lacking history.

## 5. Integration Strategy
The output of the `BehavioralEngine` (`behavioral_risk_signal`) is injected into the `decision` response dictionary at the Risk Fusion layer in `api/services.py`. In a production environment with denser data, this signal could be used to override ML decisions (e.g., if XGBoost says Low Risk, but Behavioral Deviation is extreme, upgrade to Medium Risk).

## 6. Real-Time Architecture
The prototype relies on an in-memory `collections.defaultdict`. 
For a fully distributed production deployment, this would be replaced with a low-latency Redis cluster implementing sliding window sorted sets.
