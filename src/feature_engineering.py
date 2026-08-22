import pandas as pd
import numpy as np

def engineer_features(df):
    """
    Applies behavioral feature engineering to the PaySim dataset.
    Creates new features based on domain knowledge of financial fraud.
    """
    # Use .copy() to avoid modifying the original dataframe in-place
    # when called from a Jupyter notebook.
    df = df.copy()
    
    # 1. Time-based features
    # 'step' maps to 1 hour of time. Fraudsters may operate at unusual hours.
    df['hour_of_day'] = df['step'] % 24
    
    # 2. Balance Errors
    # Often in the PaySim dataset (and real-world systems), fraudulent 
    # transactions zero out balances or have mismatched transaction logs.
    
    # Originator Balance Error
    # Theoretically: oldbalanceOrg - amount = newbalanceOrig
    # Error: newbalanceOrig + amount - oldbalanceOrg
    df['errorBalanceOrig'] = df['newbalanceOrig'] + df['amount'] - df['oldbalanceOrg']
    
    # Destination Balance Error
    # Theoretically: oldbalanceDest + amount = newbalanceDest
    # Error: oldbalanceDest + amount - newbalanceDest
    df['errorBalanceDest'] = df['oldbalanceDest'] + df['amount'] - df['newbalanceDest']
    
    return df
