# Feature Availability Analysis

## 1. Purpose
The purpose of this analysis is to rigidly enforce the boundary between what information is known *before* a financial transaction is authorized, and what information is only known *after*. Using post-transaction information to predict fraud creates Data Leakage, rendering the model useless in a live environment.

## 2. Complete Feature Inventory
| Feature Name | Source | Original/Derived | Used by Pre-Auth Model? | Leakage Risk? |
|---|---|---|---|---|
| `step` | Dataset | Original | Yes | None |
| `type` | Dataset | Original | Yes | None |
| `amount` | Dataset | Original | Yes | None |
| `oldbalanceOrg` | Dataset | Original | Yes | None |
| `oldbalanceDest`| Dataset | Original | Yes | None |
| `newbalanceOrig`| Dataset | Original | No (Dropped) | High (Post-Auth) |
| `newbalanceDest`| Dataset | Original | No (Dropped) | High (Post-Auth) |

## 3. Pre-Transaction Features (CATEGORY A)
- `step`, `type`, `oldbalanceOrg`, `oldbalanceDest`
These are known the moment the API request payload is formed.

## 4. During-Authorization Features (CATEGORY B)
- `amount`
This is parsed from the live request while authorization logic executes.

## 5. Post-Transaction Features (CATEGORY C)
- `newbalanceOrig`, `newbalanceDest`
These features *depend on the transaction succeeding*. If a transaction is blocked, these balances never update. Therefore, they are Category C and strictly forbidden from inference.

## 6. API Validation Mechanism
The `TransactionRequest` Pydantic model sets `newbalanceOrig` and `newbalanceDest` as Optional. The FastAPI route `predict` parses the payload but the ML `preprocessing.py` explicitly ignores them. The system now returns traceability metadata: `realtime_feature_validation` and `feature_schema_version`.

## 7. Research Implications
Future research must expand the dataset beyond PaySim to include Behavioral and Device-based features (see `real_time_data_requirements.md`).
