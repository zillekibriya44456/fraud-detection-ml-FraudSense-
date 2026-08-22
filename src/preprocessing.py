import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from src.feature_engineering import engineer_features

def load_and_clean_data(file_path):
    """
    Loads the PaySim dataset and removes irrelevant columns.
    Drops 'nameOrig', 'nameDest', and 'isFlaggedFraud'.
    """
    df = pd.read_csv(file_path)
    
    # We only care about TRANSFER and CASH_OUT based on EDA
    # However, keeping all types for now is also fine. Let's filter to where fraud can actually happen to save memory.
    df = df[df['type'].isin(['TRANSFER', 'CASH_OUT'])].copy()
    
    # Apply feature engineering before dropping columns or splitting
    df = engineer_features(df)
    
    # Drop columns that are high cardinality strings or irrelevant business rules
    columns_to_drop = ['nameOrig', 'nameDest', 'isFlaggedFraud']
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
    
    return df

def get_preprocessor(numeric_features, categorical_features=None):
    """
    Returns a scikit-learn ColumnTransformer that imputes and scales numerical features
    and one-hot encodes categorical features.
    """
    if categorical_features is None:
        categorical_features = ['type']
    
    # Numerical pipeline: Impute missing values with median, then scale
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # Categorical pipeline: Impute with most frequent, then one-hot encode
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    return preprocessor

def preprocess_and_split(df, val_size=0.15, test_size=0.15, random_state=42):
    """
    Splits the dataframe into train/val/test sets to prevent data leakage,
    then fits the preprocessor ONLY on the training data, and transforms all three.
    """
    X = df.drop(columns=['isFraud'])
    y = df['isFraud']
    
    # Calculate relative sizes
    test_ratio = test_size
    val_ratio = val_size / (1.0 - test_size)
    
    # First split: train+val and test
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_ratio, random_state=random_state, stratify=y
    )
    
    # Second split: train and val
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_ratio, random_state=random_state, stratify=y_temp
    )
    
    categorical_features = ['type']
    # Dynamically find numeric features to support different experiment sets
    numeric_features = [col for col in X_train.columns if col not in categorical_features]
    
    preprocessor = get_preprocessor(numeric_features, categorical_features)
    
    # FIT ONLY ON TRAINING DATA
    X_train_processed = preprocessor.fit_transform(X_train)
    X_val_processed = preprocessor.transform(X_val)
    X_test_processed = preprocessor.transform(X_test)
    
    # Get feature names
    cat_features_encoded = preprocessor.named_transformers_['cat'].named_steps['onehot'].get_feature_names_out(categorical_features)
    feature_names = numeric_features + list(cat_features_encoded)
    
    # Convert back to DataFrame
    X_train_processed_df = pd.DataFrame(X_train_processed, columns=feature_names, index=X_train.index)
    X_val_processed_df = pd.DataFrame(X_val_processed, columns=feature_names, index=X_val.index)
    X_test_processed_df = pd.DataFrame(X_test_processed, columns=feature_names, index=X_test.index)
    
    return X_train_processed_df, X_val_processed_df, X_test_processed_df, y_train, y_val, y_test, preprocessor
