# Real-Time Data Requirements

This document categorizes features into those supported by the current PaySim dataset, and those that are heavily recommended for future real-world production environments.

## A. CURRENTLY SUPPORTED BY PAYSIM DATASET
These features are immediately available and have been vetted to be free of data leakage before authorization:
- `step` (Time mapping)
- `type` (Channel)
- `amount` (Requested Transaction Value)
- `oldbalanceOrg` (Sender pre-auth balance)
- `oldbalanceDest` (Receiver pre-auth balance)

## B. FUTURE PRODUCTION DATA REQUIREMENTS
*REAL-WORLD FEATURES NOT AVAILABLE IN THE CURRENT DATASET*

> [!WARNING]
> Do NOT add these to the existing trained model as the PaySim dataset does not contain them. These are meant to inform the next generation of data collection.

### 1. Device and Session Intelligence
- **Device Fingerprint**: Has the sender used this exact physical device before?
- **IP Risk Score**: Is the IP address a known proxy/VPN or from an anomalous geolocation?
- **Session Duration**: How fast did the user log in and initiate a transfer? (Bot detection).

### 2. Behavioral History
- **Beneficiary History**: Is this the first time the sender is transferring money to this specific receiver?
- **User Transaction Velocity**: Has the sender initiated 5 other transfers in the last 10 minutes?
- **Time-of-Day Anomaly**: Is the user transacting at 3:00 AM their local time when they usually transact at noon?

### 3. Account Intelligence
- **Account Age**: Was the destination account created today?
- **Password Changes**: Was the sender's password changed in the last 24 hours prior to this transfer?
