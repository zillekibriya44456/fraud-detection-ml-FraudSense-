import pandas as pd
from src.feature_engineering import engineer_features

def test_engineer_features():
    data = {
        "step": [1, 25],
        "amount": [100.0, 50.0],
        "oldbalanceOrg": [1000.0, 50.0],
        "newbalanceOrig": [900.0, 0.0],
        "oldbalanceDest": [0.0, 200.0],
        "newbalanceDest": [100.0, 250.0]
    }
    df = pd.DataFrame(data)
    
    df_engineered = engineer_features(df)
    
    # 1. Test hour_of_day
    assert df_engineered["hour_of_day"].iloc[0] == 1
    assert df_engineered["hour_of_day"].iloc[1] == 1  # 25 % 24
    
    # 2. Test Originator Balance Error
    assert df_engineered["errorBalanceOrig"].iloc[0] == 0.0
    assert df_engineered["errorBalanceOrig"].iloc[1] == 0.0
    
    # 3. Test Destination Balance Error
    assert df_engineered["errorBalanceDest"].iloc[0] == 0.0
    assert df_engineered["errorBalanceDest"].iloc[1] == 0.0
