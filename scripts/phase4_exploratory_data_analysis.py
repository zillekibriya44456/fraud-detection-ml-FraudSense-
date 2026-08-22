"""
FraudGuard AI — Phase 4: Exploratory Data Analysis
==================================================
Executes Exploratory Data Analysis.
Produces figures and a structured summary.
Mirrors the analysis in notebooks/02_exploratory_data_analysis.ipynb.

Run with: venv/bin/python scripts/phase4_exploratory_data_analysis.py
"""

import sys
import os
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for script execution
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')

# ── Paths ───────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parent.parent
RAW         = REPO_ROOT / "data" / "raw"
FIG_DIR     = REPO_ROOT / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

PAYSIM_PATH  = RAW / "PS_20174392719_1491204439457_log.csv"

# ── Style ────────────────────────────────────────────────────────────────────
sns.set_theme(style='whitegrid')
pd.set_option('display.float_format', lambda x: '%.3f' % x)
plt.rcParams.update({
    'figure.dpi': 150,
    'figure.figsize': (10, 6),
})

SEP = "=" * 72

def main():
    print(f"\n{SEP}")
    print("  FraudGuard AI — Phase 4: Exploratory Data Analysis")
    print(f"  {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEP)

    # 1. Load Dataset
    print("\nLoading dataset...")
    try:
        df = pd.read_csv(PAYSIM_PATH, low_memory=False)
        print(f"Loaded {df.shape[0]:,} rows and {df.shape[1]} columns.")
    except FileNotFoundError:
        print("Error: Dataset not found. Please ensure it is in the data/raw/ directory.")
        return

    # 2. Transaction Types and Fraud Distribution
    print(f"\n{SEP}")
    print("  Transaction Types and Fraud Distribution")
    print(SEP)
    
    plt.figure(figsize=(10, 6))
    ax = sns.countplot(data=df, x='type', hue='isFraud')
    plt.title('Transaction Types: Legitimate vs Fraudulent')
    plt.yscale('log')
    plt.ylabel('Count (Log Scale)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'paysim_transaction_types.png', bbox_inches='tight')
    plt.close()
    print("  ✅ Figure saved: paysim_transaction_types.png")
    
    print("\nFraud counts by transaction type:")
    print(df[df['isFraud'] == 1]['type'].value_counts().to_string())

    # 3. Transaction Amount Analysis
    print(f"\n{SEP}")
    print("  Transaction Amount Analysis")
    print(SEP)
    
    df_filtered = df[df['type'].isin(['TRANSFER', 'CASH_OUT'])]
    
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df_filtered, x='isFraud', y='amount')
    plt.title('Transaction Amount Distribution: Legitimate vs Fraud')
    plt.yscale('log')
    plt.ylabel('Amount (Log Scale)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'paysim_amount_boxplot.png', bbox_inches='tight')
    plt.close()
    print("  ✅ Figure saved: paysim_amount_boxplot.png")
    
    print("\nSummary statistics for Fraudulent amounts:")
    print(df_filtered[df_filtered['isFraud'] == 1]['amount'].describe().to_string())
    print("\nSummary statistics for Legitimate amounts:")
    print(df_filtered[df_filtered['isFraud'] == 0]['amount'].describe().to_string())

    # 4. Correlation Analysis
    print(f"\n{SEP}")
    print("  Correlation Analysis")
    print(SEP)
    
    numeric_cols = df_filtered.select_dtypes(include=[np.number])
    
    plt.figure(figsize=(12, 8))
    corr = numeric_cols.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('Correlation Heatmap (TRANSFER and CASH_OUT only)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'paysim_correlation_heatmap.png', bbox_inches='tight')
    plt.close()
    print("  ✅ Figure saved: paysim_correlation_heatmap.png")
    
    # 5. Time Behavior
    print(f"\n{SEP}")
    print("  Time Behavior Analysis")
    print(SEP)
    plt.figure(figsize=(12, 6))
    sns.histplot(data=df, x='step', hue='isFraud', bins=100, element='step', common_norm=False, log_scale=(False, True))
    plt.title('Transaction Count over Time (Step = 1 hour)')
    plt.ylabel('Count (Log Scale)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'paysim_time_behavior.png', bbox_inches='tight')
    plt.close()
    print("  ✅ Figure saved: paysim_time_behavior.png")

    # 6. Feature Distributions
    print(f"\n{SEP}")
    print("  Feature Distributions")
    print(SEP)
    plt.figure(figsize=(15, 10))
    features_to_plot = ['oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest']
    for i, feature in enumerate(features_to_plot, 1):
        plt.subplot(2, 2, i)
        sns.boxplot(data=df_filtered, x='isFraud', y=feature)
        plt.title(f'{feature} by Fraud Status')
        plt.yscale('symlog')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'paysim_feature_distributions.png', bbox_inches='tight')
    plt.close()
    print("  ✅ Figure saved: paysim_feature_distributions.png")

    # 7. Missingness
    print(f"\n{SEP}")
    print("  Missingness Analysis")
    print(SEP)
    missing_data = df.isnull().sum()
    print("Missing values per column:")
    print(missing_data[missing_data > 0].to_string() if missing_data.sum() > 0 else "No missing values found.")

    # 8. Outliers
    print(f"\n{SEP}")
    print("  Outliers Analysis")
    print(SEP)
    Q1 = df_filtered['amount'].quantile(0.25)
    Q3 = df_filtered['amount'].quantile(0.75)
    IQR = Q3 - Q1
    upper_bound = Q3 + 1.5 * IQR
    outliers = df_filtered[df_filtered['amount'] > upper_bound]
    print(f"Number of outlier transactions by amount (> {upper_bound:.2f}): {len(outliers):,}")
    fraud_in_outliers = outliers['isFraud'].sum()
    print(f"Fraudulent transactions among outliers: {fraud_in_outliers:,} ({(fraud_in_outliers/len(outliers))*100:.2f}%)")
    
    # 9. Class Distribution overall
    print(f"\n{SEP}")
    print("  Overall Class Distribution")
    print(SEP)
    class_dist = df['isFraud'].value_counts()
    print(class_dist.to_string())
    print(f"Fraud Percentage: {(class_dist.get(1, 0) / len(df)) * 100:.4f}%")

    print(f"\n{SEP}")
    print("  PHASE 4 COMPLETE")
    print(SEP + "\n")

if __name__ == "__main__":
    main()
