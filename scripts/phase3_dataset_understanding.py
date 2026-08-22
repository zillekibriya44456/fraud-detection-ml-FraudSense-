"""
FraudGuard AI — Phase 3: Dataset Understanding Analysis
========================================================
Executes the full dataset understanding analysis.
Produces figures and a structured summary.
Mirrors the analysis in notebooks/01_dataset_understanding.ipynb.

Run with: venv/bin/python scripts/phase3_dataset_understanding.py
"""

import sys
import os
import warnings
import json
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for script execution
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

warnings.filterwarnings('ignore')

# ── Paths ───────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parent.parent
RAW         = REPO_ROOT / "data" / "raw"
FIG_DIR     = REPO_ROOT / "reports" / "figures"
TABLE_DIR   = REPO_ROOT / "reports" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

PAYSIM_PATH  = RAW / "PS_20174392719_1491204439457_log.csv"
ULB_PATH     = RAW / "creditcard.csv"
IEEE_TX_PATH = RAW / "IEEE_CIS archive (3)" / "train_transaction.csv"
IEEE_ID_PATH = RAW / "IEEE_CIS archive (3)" / "train_identity.csv"

# ── Style ────────────────────────────────────────────────────────────────────
sns.set_theme(style='whitegrid', palette='muted')
plt.rcParams.update({
    'figure.dpi': 150,
    'figure.figsize': (10, 5),
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
})
COLORS = {'legit': '#4CAF50', 'fraud': '#F44336',
          'primary': '#2196F3', 'benchmark': '#4CAF50',
          'secondary': '#FF9800', 'rejected': '#9E9E9E'}

SEP = "=" * 72
findings = {}  # accumulate all findings for JSON summary


# ─────────────────────────────────────────────────────────────────────────────
# 1. PAYSIM
# ─────────────────────────────────────────────────────────────────────────────
def analyse_paysim():
    print(f"\n{SEP}")
    print("  PAYSIM (PRIMARY)")
    print(SEP)

    df = pd.read_csv(PAYSIM_PATH, low_memory=False)
    n_rows, n_cols = df.shape
    print(f"  Shape: {n_rows:,} × {n_cols}")

    # Schema
    schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
    print(f"\n  Schema:\n{df.dtypes.to_string()}")

    # Missing
    missing = df.isnull().sum()
    total_missing = int(missing.sum())
    print(f"\n  Missing values: {total_missing}")

    # Target distribution
    vc = df['isFraud'].value_counts().sort_index()
    fraud_count = int(vc.get(1, 0))
    legit_count = int(vc.get(0, 0))
    fraud_pct   = fraud_count / n_rows * 100
    print(f"\n  Target (isFraud):")
    print(f"    Legitimate: {legit_count:,}")
    print(f"    Fraud:      {fraud_count:,}  ({fraud_pct:.4f}%)")

    # Transaction type analysis
    type_fraud = df.groupby('type')['isFraud'].agg(
        fraud_count='sum', total='count'
    ).reset_index()
    type_fraud['fraud_rate_pct'] = type_fraud['fraud_count'] / type_fraud['total'] * 100
    type_fraud = type_fraud.sort_values('fraud_count', ascending=False)
    print(f"\n  Fraud by transaction type:\n{type_fraud.to_string(index=False)}")

    # Descriptive stats
    num_cols = ['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig',
                'oldbalanceDest', 'newbalanceDest']
    desc = df[num_cols].describe().round(2)

    # Identifier cardinality
    id_cardinality = {
        'nameOrig': int(df['nameOrig'].nunique()),
        'nameDest': int(df['nameDest'].nunique()),
    }
    print(f"\n  Identifier cardinality:")
    for col, n in id_cardinality.items():
        print(f"    {col}: {n:,} unique values")

    # isFlaggedFraud analysis
    flagged = int((df['isFlaggedFraud'] == 1).sum())
    print(f"\n  isFlaggedFraud == 1: {flagged:,}  (business rule: amount > 200,000)")

    # ── Figure 1: Class distribution ────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Bar chart
    ax = axes[0]
    bars = ax.bar(['Legitimate', 'Fraud'],
                  [legit_count, fraud_count],
                  color=[COLORS['legit'], COLORS['fraud']],
                  edgecolor='white', linewidth=0.8, width=0.5)
    ax.set_yscale('log')
    ax.set_title('PaySim — Class Distribution (Log Scale)')
    ax.set_ylabel('Transaction Count (Log Scale)')
    for bar, val in zip(bars, [legit_count, fraud_count]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.3,
                f'{val:,}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Pie chart
    ax2 = axes[1]
    ax2.pie([legit_count, fraud_count],
            labels=[f'Legitimate\n{legit_count:,}\n(99.87%)',
                    f'Fraud\n{fraud_count:,}\n(0.13%)'],
            colors=[COLORS['legit'], COLORS['fraud']],
            explode=[0, 0.1], autopct='%1.3f%%', startangle=90,
            textprops={'fontsize': 10})
    ax2.set_title('PaySim — Fraud vs Legitimate Proportion')

    plt.suptitle('PaySim Dataset — Class Balance Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'paysim_class_distribution.png', bbox_inches='tight')
    plt.close()
    print(f"\n  ✅ Figure saved: paysim_class_distribution.png")

    # ── Figure 2: Fraud by transaction type ────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax1 = axes[0]
    colors_type = [COLORS['fraud'] if r > 0 else COLORS['legit']
                   for r in type_fraud['fraud_count']]
    bars2 = ax1.barh(type_fraud['type'], type_fraud['total'],
                     color='#E0E0E0', edgecolor='white', label='Total')
    bars3 = ax1.barh(type_fraud['type'], type_fraud['fraud_count'],
                     color=COLORS['fraud'], edgecolor='white', label='Fraud')
    ax1.set_xlabel('Transaction Count')
    ax1.set_title('PaySim — Transaction Volume by Type')
    ax1.legend()
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))

    ax2 = axes[1]
    bars4 = ax2.barh(type_fraud['type'], type_fraud['fraud_rate_pct'],
                     color=[COLORS['fraud'] if r > 0 else COLORS['legit']
                            for r in type_fraud['fraud_count']],
                     edgecolor='white')
    for bar, val in zip(bars4, type_fraud['fraud_rate_pct']):
        ax2.text(val + 0.05, bar.get_y() + bar.get_height()/2,
                 f'{val:.2f}%', va='center', fontsize=10)
    ax2.set_xlabel('Fraud Rate (%)')
    ax2.set_title('PaySim — Fraud Rate by Transaction Type')

    plt.suptitle('PaySim — Fraud Distribution by Transaction Type', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'paysim_fraud_by_type.png', bbox_inches='tight')
    plt.close()
    print(f"  ✅ Figure saved: paysim_fraud_by_type.png")

    # ── Figure 3: Amount distributions ────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    fraud_amounts  = df[df['isFraud'] == 1]['amount']
    legit_amounts  = df[df['isFraud'] == 0]['amount'].sample(
        min(50000, len(df[df['isFraud'] == 0])), random_state=42)

    ax1 = axes[0]
    ax1.hist(np.log1p(legit_amounts), bins=60, alpha=0.6,
             color=COLORS['legit'], label='Legitimate', density=True)
    ax1.hist(np.log1p(fraud_amounts), bins=60, alpha=0.8,
             color=COLORS['fraud'], label='Fraud', density=True)
    ax1.set_xlabel('log(1 + Amount)')
    ax1.set_ylabel('Density')
    ax1.set_title('PaySim — Amount Distribution (log scale)')
    ax1.legend()

    ax2 = axes[1]
    ax2.boxplot([np.log1p(legit_amounts), np.log1p(fraud_amounts)],
                tick_labels=['Legitimate', 'Fraud'],
                patch_artist=True,
                boxprops=dict(facecolor='#E3F2FD'),
                medianprops=dict(color='navy', linewidth=2))
    ax2.set_ylabel('log(1 + Amount)')
    ax2.set_title('PaySim — Amount Boxplot (log scale)')

    plt.suptitle('PaySim — Transaction Amount: Fraud vs Legitimate', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'paysim_amount_distribution.png', bbox_inches='tight')
    plt.close()
    print(f"  ✅ Figure saved: paysim_amount_distribution.png")

    # ── Save table ──────────────────────────────────────────────────────────
    type_fraud.to_csv(TABLE_DIR / 'paysim_fraud_by_type.csv', index=False)
    desc.to_csv(TABLE_DIR / 'paysim_descriptive_stats.csv')

    findings['paysim'] = {
        'rows': n_rows, 'cols': n_cols,
        'fraud_count': fraud_count, 'legit_count': legit_count,
        'fraud_pct': round(fraud_pct, 4),
        'total_missing': total_missing,
        'id_cardinality': id_cardinality,
        'flagged_fraud_rule_count': flagged,
        'fraud_types': type_fraud[type_fraud['fraud_count'] > 0]['type'].tolist(),
        'leakage_columns': ['nameOrig', 'nameDest', 'isFlaggedFraud'],
        'leakage_risk': 'LOW (identified and documented)',
    }

    del df
    print(f"\n  PaySim analysis complete ✅")


# ─────────────────────────────────────────────────────────────────────────────
# 2. ULB CREDIT CARD
# ─────────────────────────────────────────────────────────────────────────────
def analyse_ulb():
    print(f"\n{SEP}")
    print("  ULB CREDIT CARD (BENCHMARK)")
    print(SEP)

    df = pd.read_csv(ULB_PATH, low_memory=False)
    n_rows, n_cols = df.shape
    print(f"  Shape: {n_rows:,} × {n_cols}")
    print(f"\n  Schema:\n{df.dtypes.to_string()}")

    missing = int(df.isnull().sum().sum())
    dupes   = int(df.duplicated().sum())
    print(f"\n  Missing values: {missing}")
    print(f"  Duplicate rows: {dupes:,}")

    vc = df['Class'].value_counts().sort_index()
    fraud_count = int(vc.get(1, 0))
    legit_count = int(vc.get(0, 0))
    fraud_pct   = fraud_count / n_rows * 100
    print(f"\n  Target (Class):")
    print(f"    Legitimate: {legit_count:,}")
    print(f"    Fraud:      {fraud_count:,}  ({fraud_pct:.4f}%)")

    desc_interp = df[['Time', 'Amount']].describe().round(2)
    print(f"\n  Interpretable features (Time, Amount):\n{desc_interp.to_string()}")

    # ── Figure ──────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Class distribution
    ax = axes[0]
    bars = ax.bar(['Legitimate', 'Fraud'], [legit_count, fraud_count],
                  color=[COLORS['legit'], COLORS['fraud']],
                  edgecolor='white', linewidth=0.8, width=0.5)
    ax.set_yscale('log')
    ax.set_title('Class Distribution (Log Scale)')
    ax.set_ylabel('Count (Log Scale)')
    for bar, val in zip(bars, [legit_count, fraud_count]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.3,
                f'{val:,}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Amount distribution
    ax2 = axes[1]
    ax2.hist(np.log1p(df[df['Class'] == 0]['Amount']), bins=60, alpha=0.6,
             color=COLORS['legit'], label='Legitimate', density=True)
    ax2.hist(np.log1p(df[df['Class'] == 1]['Amount']), bins=30, alpha=0.8,
             color=COLORS['fraud'], label='Fraud', density=True)
    ax2.set_xlabel('log(1 + Amount)')
    ax2.set_ylabel('Density')
    ax2.set_title('Amount Distribution (log scale)')
    ax2.legend()

    # Time distribution
    ax3 = axes[2]
    ax3.hist(df[df['Class'] == 0]['Time'] / 3600, bins=48, alpha=0.5,
             color=COLORS['legit'], label='Legitimate', density=True)
    ax3.hist(df[df['Class'] == 1]['Time'] / 3600, bins=24, alpha=0.8,
             color=COLORS['fraud'], label='Fraud', density=True)
    ax3.set_xlabel('Time (hours from start)')
    ax3.set_ylabel('Density')
    ax3.set_title('Time Distribution')
    ax3.legend()

    plt.suptitle('ULB Credit Card — Dataset Understanding', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'ulb_dataset_understanding.png', bbox_inches='tight')
    plt.close()
    print(f"\n  ✅ Figure saved: ulb_dataset_understanding.png")

    desc_interp.to_csv(TABLE_DIR / 'ulb_descriptive_stats.csv')

    findings['ulb'] = {
        'rows': n_rows, 'cols': n_cols,
        'fraud_count': fraud_count, 'legit_count': legit_count,
        'fraud_pct': round(fraud_pct, 4),
        'total_missing': missing,
        'duplicate_rows': dupes,
        'interpretable_features': ['Time', 'Amount'],
        'anonymised_features': [f'V{i}' for i in range(1, 29)],
        'explainability_possible': False,
        'duplicate_handling': 'Remove from TRAIN set only during preprocessing',
    }

    del df
    print(f"\n  ULB analysis complete ✅")


# ─────────────────────────────────────────────────────────────────────────────
# 3. IEEE-CIS (SAMPLE ONLY — too large for full load)
# ─────────────────────────────────────────────────────────────────────────────
def analyse_ieee():
    print(f"\n{SEP}")
    print("  IEEE-CIS FRAUD DETECTION (SECONDARY) — sample only")
    print(SEP)

    # Load sample for schema
    df_sample = pd.read_csv(IEEE_TX_PATH, nrows=50_000, low_memory=False)
    n_sample, n_cols = df_sample.shape
    print(f"  Sample shape: {n_sample:,} × {n_cols} (full: 590,540 rows)")

    # Column groups
    cols = list(df_sample.columns)
    c_cols = [c for c in cols if c.startswith('C') and c[1:].isdigit()]
    d_cols = [c for c in cols if c.startswith('D') and c[1:].isdigit()]
    m_cols = [c for c in cols if c.startswith('M') and c[1:].isdigit()]
    v_cols = [c for c in cols if c.startswith('V') and c[1:].isdigit()]
    cat_cols = ['ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain']
    id_cols  = ['TransactionID', 'TransactionDT']

    print(f"\n  Column groups:")
    print(f"    Identifiers:   {id_cols}")
    print(f"    Categorical:   {cat_cols}")
    print(f"    C (count):     {len(c_cols)} cols ({c_cols[0]}..{c_cols[-1]})")
    print(f"    D (timedelta): {len(d_cols)} cols ({d_cols[0]}..{d_cols[-1]})")
    print(f"    M (match):     {len(m_cols)} cols ({m_cols[0]}..{m_cols[-1]})")
    print(f"    V (Vesta):     {len(v_cols)} cols ({v_cols[0]}..{v_cols[-1]})")

    # Missing in sample
    miss = df_sample.isnull().sum()
    miss_pct = miss / len(df_sample) * 100
    miss_df = pd.DataFrame({'count': miss, 'pct': miss_pct})
    miss_df = miss_df[miss_df['count'] > 0].sort_values('pct', ascending=False)
    print(f"\n  Columns with missing (in sample): {len(miss_df)}/{n_cols}")
    print(f"  Top 10 most missing:")
    print(miss_df.head(10).to_string())

    # Target in sample
    vc = df_sample['isFraud'].value_counts().sort_index()
    fraud_s = int(vc.get(1, 0))
    legit_s = int(vc.get(0, 0))
    print(f"\n  Target (isFraud) in sample: {legit_s:,} legit, {fraud_s:,} fraud")
    print(f"  Full dataset fraud rate: 3.499% (from Phase 2 verification)")

    # Identity file
    df_id = pd.read_csv(IEEE_ID_PATH, nrows=5, low_memory=False)
    id_cols_list = list(df_id.columns)
    print(f"\n  Identity file columns ({len(id_cols_list)}): {id_cols_list[:5]}...")

    # ── Figure: Missingness heatmap ─────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Top 30 missing columns
    ax1 = axes[0]
    top30 = miss_df.head(30)
    ax1.barh(top30.index[::-1], top30['pct'][::-1],
             color='#FF7043', edgecolor='white')
    ax1.set_xlabel('Missing %')
    ax1.set_title('IEEE-CIS — Top 30 Columns by Missing %\n(in 50K row sample)')
    ax1.axvline(50, color='navy', linestyle='--', linewidth=1, label='50% threshold')
    ax1.legend()
    ax1.tick_params(axis='y', labelsize=7)

    # Column group sizes
    ax2 = axes[1]
    groups = {
        'Identifiers\n(2)': 2,
        'Categorical\n(5+)': 7,
        'Card\nInfo (6)': 6,
        'C cols\n(14)': len(c_cols),
        'D cols\n(15)': len(d_cols),
        'M cols\n(9)': len(m_cols),
        'V cols\n(339)': len(v_cols),
    }
    ax2.bar(list(groups.keys()), list(groups.values()),
            color=sns.color_palette('muted', len(groups)),
            edgecolor='white')
    ax2.set_ylabel('Number of Columns')
    ax2.set_title(f'IEEE-CIS — Column Groups\n(Total: {n_cols} columns)')
    for i, (k, v) in enumerate(groups.items()):
        ax2.text(i, v + 1, str(v), ha='center', fontsize=10, fontweight='bold')

    plt.suptitle('IEEE-CIS Transaction Dataset — Schema Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'ieee_cis_schema_analysis.png', bbox_inches='tight')
    plt.close()
    print(f"\n  ✅ Figure saved: ieee_cis_schema_analysis.png")

    miss_df.head(50).to_csv(TABLE_DIR / 'ieee_cis_top_missing_columns.csv')

    findings['ieee_cis'] = {
        'tx_rows': 590_540, 'tx_cols': n_cols,
        'id_rows': 144_233, 'id_cols': 41,
        'fraud_count': 20_663, 'legit_count': 569_877,
        'fraud_pct': 3.499,
        'column_groups': {
            'V_cols': len(v_cols), 'C_cols': len(c_cols),
            'D_cols': len(d_cols), 'M_cols': len(m_cols),
        },
        'columns_with_missing_in_sample': len(miss_df),
        'join_key': 'TransactionID',
        'data_engineering_complexity': 'HIGH',
    }

    del df_sample, df_id
    print(f"\n  IEEE-CIS analysis complete ✅")


# ─────────────────────────────────────────────────────────────────────────────
# 4. CROSS-DATASET COMPARISON FIGURES
# ─────────────────────────────────────────────────────────────────────────────
def cross_dataset_figures():
    print(f"\n{SEP}")
    print("  CROSS-DATASET COMPARISON FIGURES")
    print(SEP)

    # ── Figure: Fraud rate comparison ───────────────────────────────────────
    datasets   = ['PaySim\n(PRIMARY)', 'ULB Credit Card\n(BENCHMARK)',
                  'IEEE-CIS\n(SECONDARY)', 'UPI Fraud\n(REJECTED)']
    fraud_pcts = [0.1291, 0.1727, 3.499, 17.22]
    total_rows = [6_362_620, 284_807, 590_540, 26_393]
    colors_ds  = [COLORS['primary'], COLORS['benchmark'],
                  COLORS['secondary'], COLORS['rejected']]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax1 = axes[0]
    bars = ax1.barh(datasets[::-1], fraud_pcts[::-1],
                    color=colors_ds[::-1], edgecolor='white', linewidth=0.5)
    ax1.axvline(x=5, color='red', linestyle='--', linewidth=1.5,
                label='5% — above this is\nnon-representative')
    ax1.set_xlabel('Fraud Rate (%)')
    ax1.set_title('Fraud Rate Comparison\n(lower = more representative)')
    ax1.legend(fontsize=9)
    for bar, pct in zip(bars, fraud_pcts[::-1]):
        ax1.text(pct + 0.2, bar.get_y() + bar.get_height()/2,
                 f'{pct:.2f}%', va='center', fontsize=10, fontweight='bold')

    ax2 = axes[1]
    bars2 = ax2.barh(datasets[::-1],
                     [r/1e6 for r in total_rows[::-1]],
                     color=colors_ds[::-1], edgecolor='white', linewidth=0.5)
    ax2.set_xlabel('Total Transactions (Millions)')
    ax2.set_title('Dataset Size Comparison\n(total transactions)')
    for bar, val in zip(bars2, total_rows[::-1]):
        label = f'{val/1e6:.2f}M' if val >= 1e6 else f'{val:,}'
        ax2.text(val/1e6 + 0.02, bar.get_y() + bar.get_height()/2,
                 label, va='center', fontsize=10, fontweight='bold')

    plt.suptitle('FraudGuard AI — Dataset Comparison\n(Phase 3 Summary)', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'dataset_comparison_overview.png', bbox_inches='tight')
    plt.close()
    print(f"  ✅ Figure saved: dataset_comparison_overview.png")

    # ── Figure: Class imbalance severity ────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))

    imbalance_ratios = [773, 578, 28, 6]   # Legit:Fraud
    bars3 = ax.bar(datasets, imbalance_ratios,
                   color=colors_ds, edgecolor='white', linewidth=0.8)
    ax.set_ylabel('Imbalance Ratio (Legitimate : Fraud)')
    ax.set_title('Class Imbalance Severity by Dataset\n'
                 '(higher ratio = more extreme = harder for ML)',
                 fontsize=13, fontweight='bold')
    for bar, val in zip(bars3, imbalance_ratios):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f'{val}:1', ha='center', fontsize=11, fontweight='bold')
    ax.axhline(100, color='orange', linestyle='--', linewidth=1.5,
               label='100:1 reference line')
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'dataset_imbalance_severity.png', bbox_inches='tight')
    plt.close()
    print(f"  ✅ Figure saved: dataset_imbalance_severity.png")


# ─────────────────────────────────────────────────────────────────────────────
# 5. LEAKAGE REGISTER TABLE
# ─────────────────────────────────────────────────────────────────────────────
def produce_leakage_register():
    leakage = [
        {'Dataset': 'PaySim', 'Column': 'nameOrig',
         'Type': 'Identifier leakage', 'Action': 'DROP before training'},
        {'Dataset': 'PaySim', 'Column': 'nameDest',
         'Type': 'Identifier leakage', 'Action': 'DROP before training'},
        {'Dataset': 'PaySim', 'Column': 'isFlaggedFraud',
         'Type': 'Rule-based derivation (not ML)', 'Action': 'DROP before training'},
        {'Dataset': 'All', 'Column': 'Target column',
         'Type': 'Target leakage', 'Action': 'Use as y only, never as X feature'},
        {'Dataset': 'IEEE-CIS', 'Column': 'TransactionID',
         'Type': 'Identifier', 'Action': 'DROP or use as join key only'},
        {'Dataset': 'IEEE-CIS', 'Column': 'TransactionDT',
         'Type': 'Timestamp — potential temporal leakage',
         'Action': 'Transform to relative time features, not raw value'},
    ]
    df_leak = pd.DataFrame(leakage)
    df_leak.to_csv(TABLE_DIR / 'leakage_register.csv', index=False)
    print(f"\n  ✅ Table saved: leakage_register.csv")
    findings['leakage_register'] = leakage


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{SEP}")
    print("  FraudGuard AI — Phase 3: Dataset Understanding")
    print(f"  {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEP)

    analyse_paysim()
    analyse_ulb()
    analyse_ieee()
    cross_dataset_figures()
    produce_leakage_register()

    # Save findings JSON
    out = REPO_ROOT / "reports" / "phase3_dataset_understanding.json"
    with open(out, 'w') as f:
        json.dump(findings, f, indent=4, default=str)

    print(f"\n{SEP}")
    print("  PHASE 3 SUMMARY")
    print(SEP)
    print(f"  Figures saved to: {FIG_DIR}")
    print(f"  Tables saved to : {TABLE_DIR}")
    print(f"  Findings JSON   : {out}")
    print(f"\n  Figures produced:")
    for fig_file in sorted(FIG_DIR.glob("*.png")):
        print(f"    {fig_file.name}")
    print(SEP + "\n")


if __name__ == "__main__":
    main()
