# Model Drift and Performance Monitoring Research

## 1. The Fraud Pattern Evolution Problem
Financial fraud is inherently adversarial. As soon as a model is deployed to catch a specific type of fraud (e.g., massive transfers to new accounts), fraudsters adapt their behavior to bypass the model (e.g., performing many small transfers just below the threshold). This leads to a decline in model effectiveness over time.

## 2. Feature Drift
Feature drift (Covariate Shift) occurs when the distribution of input features changes over time. 
For example, if the average transaction `amount` in the training dataset was $500, but during the holidays it spikes to $2,500, the model is operating outside its trained distribution. 
**Implemented Methodology**: We calculate the Population Stability Index (PSI) by comparing the binned probability distribution of incoming live data against the baseline distribution calculated from the training set.

## 3. Prediction Drift
Prediction Drift occurs when the output of the model changes significantly.
If the model historically predicted 0.5% of transactions as fraud, but suddenly starts predicting 15% as fraud, it indicates a severe issue—either massive fraud attack or, more likely, a broken upstream data pipeline feeding corrupted data to the model.
**Implemented Methodology**: PSI is also applied to the output `fraud_probability`.

## 4. Concept Drift
Concept Drift occurs when the underlying definition of the target variable changes. In fraud, this means what *was* considered legitimate behavior is now being used for fraud, or vice-versa. Feature distributions might remain identical, but the relationship between features and the target changes.

## 5. Delayed Fraud Labels
In real-world fraud detection, ground-truth labels (Chargebacks, Fraud Reports) take 30 to 90 days to arrive. 
**Implemented Methodology**: We bridge this gap by utilizing the Case Management system. When analysts resolve a case as `CONFIRMED_FRAUD` or `FALSE_POSITIVE`, we use this as a proxy label to compute live performance metrics.

## 6. Performance Monitoring
Using the proxy labels from resolved cases, we calculate **Precision**. 
We cannot accurately calculate **Recall** (False Negative Rate) purely from cases, because we only investigate transactions we already flagged (`BLOCK`/`VERIFY`). Unflagged (`APPROVE`) transactions that turn out to be fraud are invisible to the system until external chargeback data is ingested.

## 7. Controlled Retraining
**Critical Rule**: Models should never be automatically retrained and deployed without human oversight in a financial setting.
**Implemented Methodology**: The Model Registry evaluates Feature Drift, Prediction Drift, and Live Precision. It outputs a recommendation: `NO ACTION`, `MONITOR`, `REVIEW REQUIRED`, or `RETRAINING RECOMMENDED`. A Data Scientist must then manually trigger the CI/CD training pipeline.

## 8. Limitations and Threats to Validity
- **Sample Size**: PSI and Precision metrics are highly volatile with small sample sizes. We implemented a `min_sample_size` rule to output `INSUFFICIENT_DATA` rather than false alarms.
- **Selection Bias in Labels**: Because we only compute Precision on transactions the model *already suspected*, the metric is biased. It does not represent the model's accuracy on the global population of transactions.
