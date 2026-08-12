import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

def load_and_clean_data(file_path):
    """
    Loads the PaySim dataset and removes irrelevant columns.
    Drops 'nameOrig', 'nameDest', and 'isFlaggedFraud'.
    """
    df = pd.read_csv(file_path)
    
    # Drop columns that are high cardinality strings or irrelevant business rules
    columns_to_drop = ['nameOrig', 'nameDest', 'isFlaggedFraud']
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
    
    return df

def get_preprocessor():
    """
    Returns a scikit-learn ColumnTransformer that scales numerical features
    and one-hot encodes categorical features.
    """
    # Define numerical and categorical columns
    numeric_features = ['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 
                        'oldbalanceDest', 'newbalanceDest']
    categorical_features = ['type']
    
    # Use StandardScaler for numeric (RobustScaler is also an option for outliers)
    # Use OneHotEncoder for 'type' (CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER)
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(drop='first', sparse_output=False), categorical_features)
        ])
    
    return preprocessor

def preprocess_and_split(df, test_size=0.2, random_state=42):
    """
    Splits the dataframe into train/test sets to prevent data leakage,
    then fits the preprocessor ONLY on the training data, and transforms both.
    """
    X = df.drop(columns=['isFraud'])
    y = df['isFraud']
    
    # Split first to prevent data leakage
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    preprocessor = get_preprocessor()
    
    # FIT ONLY ON TRAINING DATA to prevent information leakage from test set
    X_train_processed = preprocessor.fit_transform(X_train)
    
    # TRANSFORM ONLY on test data
    X_test_processed = preprocessor.transform(X_test)
    
    # Get feature names for the resulting processed arrays
    cat_features_encoded = preprocessor.named_transformers_['cat'].get_feature_names_out(categorical_features)
    feature_names = numeric_features = ['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 
                        'oldbalanceDest', 'newbalanceDest'] + list(cat_features_encoded)
    
    # Convert back to DataFrame for easier inspection
    X_train_processed_df = pd.DataFrame(X_train_processed, columns=feature_names)
    X_test_processed_df = pd.DataFrame(X_test_processed, columns=feature_names)
    
    return X_train_processed_df, X_test_processed_df, y_train, y_test, preprocessor
