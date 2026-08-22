# Feature Availability Analysis

## Real-Time Pre-Transaction Fraud Risk Assessment

This document analyzes the availability of features in the PaySim dataset within the context of a real-time, pre-authorization fraud prevention system.

The core engineering constraint is that a machine learning model cannot use information that hasn't happened yet to make a decision. In traditional fraud datasets, features are often aggregated post-transaction, leading to data leakage if not carefully modeled.

### Categorization Key
- **CATEGORY A (PRE-TRANSACTION AVAILABLE):** Features realistically available before authorization. Safe for real-time inference.
- **CATEGORY B (AVAILABLE DURING AUTHORIZATION):** Features derived during the payment processing window. Safe for real-time inference.
- **CATEGORY C (POST-TRANSACTION):** Features only reliably available after transaction completion. UNSAFE for pre-authorization.

---

## Feature Audit Table

| Feature | Current Use | Availability Stage | Real-Time Suitable? | Reason | Keep/Remove for Pre-Auth Model |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `step` (hour_of_day) | Behavioral timing | CATEGORY A | ✅ Yes | The timestamp/hour is known when the transaction is initiated. | Keep |
| `type` | Transaction method | CATEGORY A | ✅ Yes | The method (TRANSFER, CASH_OUT) is inherently known at initiation. | Keep |
| `amount` | Transaction value | CATEGORY A | ✅ Yes | The requested amount is the primary payload of the authorization request. | Keep |
| `oldbalanceOrg` | Sender balance prior | CATEGORY A | ✅ Yes | The bank knows the sender's current balance before processing the request. | Keep |
| `oldbalanceDest`| Receiver balance prior | CATEGORY A | ✅ Yes | The receiving bank knows the destination's current balance before clearing. | Keep |
| `newbalanceOrig`| Sender balance after | **CATEGORY C** | ❌ No | This is the result of the transaction. Including it leaks the outcome to the model. | **Remove** |
| `newbalanceDest`| Receiver balance after | **CATEGORY C** | ❌ No | This is the result of the transaction. Including it leaks the outcome. | **Remove** |
| `errorBalanceOrig`| Engineered balance mismatch | **CATEGORY C** | ❌ No | Mathematically derived using `newbalanceOrig`. Represents a post-transaction accounting error. | **Remove** |
| `errorBalanceDest`| Engineered balance mismatch | **CATEGORY C** | ❌ No | Mathematically derived using `newbalanceDest`. Represents a post-transaction accounting error. | **Remove** |

## Conclusion
The current full-feature model heavily relies on `newbalanceOrig`, `newbalanceDest`, and their derived error features (`errorBalanceOrig`, `errorBalanceDest`) to achieve high accuracy. 

However, in a true pre-authorization pipeline, these features constitute **Target/Future Leakage**. A separate **Pre-Authorization Model** must be trained omitting these Category C features to accurately reflect the real-world predictive power of the system prior to payment clearance.
