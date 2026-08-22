import pandas as pd

def engineer_realtime_features(df):
    """
    Applies behavioral feature engineering using ONLY features
    that are realistically available before transaction authorization.
    (Excludes newbalanceOrig and newbalanceDest)
    """
    df = df.copy()
    
    # Time-based features
    if 'step' in df.columns:
        df['hour_of_day'] = df['step'] % 24
        
    # Real-time behavioral flags (Safe before transaction clears)
    # E.g. Does the transaction empty the entire account?
    if 'amount' in df.columns and 'oldbalanceOrg' in df.columns:
        # Avoid division by zero
        df['amount_to_balance_ratio'] = df['amount'] / (df['oldbalanceOrg'] + 1e-6)
        # Is the requested amount literally all their money?
        df['emptying_account'] = (df['amount'] >= df['oldbalanceOrg']).astype(int)
        
    return df
