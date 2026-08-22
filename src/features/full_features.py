import pandas as pd
from src.features.realtime_features import engineer_realtime_features

def engineer_full_features(df):
    """
    Applies full behavioral feature engineering including post-transaction 
    features (newbalanceOrig, newbalanceDest) used by the original model.
    Contains potential target leakage but used for the baseline comparison.
    """
    # First get the safe features
    df = engineer_realtime_features(df)
    
    # Now add the unsafe / post-transaction features
    if all(col in df.columns for col in ['newbalanceOrig', 'amount', 'oldbalanceOrg']):
        df['errorBalanceOrig'] = df['newbalanceOrig'] + df['amount'] - df['oldbalanceOrg']
        
    if all(col in df.columns for col in ['oldbalanceDest', 'amount', 'newbalanceDest']):
        df['errorBalanceDest'] = df['oldbalanceDest'] + df['amount'] - df['newbalanceDest']
        
    return df
