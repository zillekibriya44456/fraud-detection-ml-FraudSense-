# Data Leakage Audit: Bank Account Fraud Detection

**Dataset**: `Base.csv`
**Target**: `fraud_bool`

## Feature Assessment

| Feature | Classification | Rationale | Action |
| :--- | :--- | :--- | :--- |
| `income` | SAFE | Normalized applicant income. Available at application time. | RETAINED |
| `name_email_similarity` | SAFE | Similarity score between name and email. Available at request time. | RETAINED |
| `prev_address_months_count` | SAFE | Months at previous address. KYC data. | RETAINED |
| `current_address_months_count` | SAFE | Months at current address. KYC data. | RETAINED |
| `customer_age` | SAFE | Applicant age. KYC data. | RETAINED |
| `days_since_request` | SAFE | Days since initial request. Available at time of scoring. | RETAINED |
| `intended_balcon_amount` | SAFE | Intended balance/amount transferred in. Available at time of request. | RETAINED |
| `payment_type` | SAFE | Payment channel type. Available at request. | RETAINED |
| `zip_count_4w` | SAFE | Zip code request frequency in 4 weeks. Velocity feature, available at scoring. | RETAINED |
| `velocity_6h` | SAFE | Number of requests in 6h window. Pre-decision velocity signal. | RETAINED |
| `velocity_24h` | SAFE | Number of requests in 24h window. Pre-decision velocity signal. | RETAINED |
| `velocity_4w` | SAFE | Number of requests in 4w window. Pre-decision velocity signal. | RETAINED |
| `bank_branch_count_8w` | SAFE | Unique bank branch visits in 8 weeks. Available at scoring. | RETAINED |
| `date_of_birth_distinct_emails_4w` | SAFE | Distinct emails with same DOB in 4w. Identity signal. | RETAINED |
| `employment_status` | SAFE | Employment category. KYC data. | RETAINED |
| `credit_risk_score` | SAFE | Bureau credit risk score. Available at decision time. | RETAINED |
| `email_is_free` | SAFE | Free email provider flag. Available at request. | RETAINED |
| `housing_status` | SAFE | Applicant housing type. KYC data. | RETAINED |
| `phone_home_valid` | SAFE | Home phone validation flag. Available at scoring. | RETAINED |
| `phone_mobile_valid` | SAFE | Mobile phone validation flag. Available at scoring. | RETAINED |
| `bank_months_count` | SAFE | Months with current bank. KYC/CRM data. | RETAINED |
| `has_other_cards` | SAFE | Whether applicant holds other cards. Bureau data. | RETAINED |
| `proposed_credit_limit` | SAFE | Proposed credit limit at application. Available at request. | RETAINED |
| `foreign_request` | SAFE | Whether request originated from foreign IP. | RETAINED |
| `source` | SAFE | Request source (INTERNET, TELEAPP, etc.). | RETAINED |
| `session_length_in_minutes` | SAFE | Session duration. Available at decision time. | RETAINED |
| `device_os` | SAFE | Device operating system. Client signal. | RETAINED |
| `keep_alive_session` | SAFE | Session keep-alive flag. Client behavioral signal. | RETAINED |
| `device_distinct_emails_8w` | SAFE | Distinct emails from device in 8 weeks. Device fingerprint signal. | RETAINED |
| `device_fraud_count` | **POTENTIAL_LEAKAGE** | Historical fraud count on device. If computed on post-decision data, it could leak. Treated as safe if computed on prior transactions only. | RETAINED (with caution) |
| `month` | SAFE | Month of request (seasonality). | RETAINED |

## Leakage Prevention Protocol
- No post-decision or outcome-dependent features identified.
- `device_fraud_count` is the only borderline feature; treated as pre-computed historical signal.
- Stratified 70/15/15 split applied before preprocessing.
- Preprocessor fitted strictly on training data.
