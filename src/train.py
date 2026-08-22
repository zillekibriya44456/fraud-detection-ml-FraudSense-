import os
import sys
import joblib
import xgboost as xgb
import logging
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure modules can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.preprocessing import load_and_clean_data, preprocess_and_split
from src.evaluate import evaluate_model

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw/PS_20174392719_1491204439457_log.csv'))
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models'))
MODEL_PATH = os.path.join(MODEL_DIR, 'xgboost_fraud_model.json')
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, 'preprocessor.joblib')

def main():
    logger.info("Loading dataset from %s", DATA_PATH)
    if not os.path.exists(DATA_PATH):
        logger.error("Dataset not found.")
        return
        
    df = load_and_clean_data(DATA_PATH)
    logger.info("Dataset loaded. Shape: %s", df.shape)
    
    logger.info("Preprocessing and splitting data...")
    X_train, X_val, X_test, y_train, y_val, y_test, preprocessor = preprocess_and_split(df)
    
    # Calculate scale_pos_weight to handle class imbalance
    # Ratio of negative class to positive class
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    logger.info("Training XGBoost model (scale_pos_weight=%.2f)...", scale_pos_weight)
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        eval_metric='logloss',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=10
    )
    
    logger.info("Evaluating on Test Set...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # Evaluate (disable plotting to prevent blocking)
    import matplotlib
    matplotlib.use('Agg') 
    metrics = evaluate_model(y_test, y_pred, y_prob, model_name="XGBoost Fraud Model")
    logger.info("Test Metrics: %s", metrics)
    
    # Save artifacts
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_model(MODEL_PATH)
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    logger.info("Artifacts saved to %s", MODEL_DIR)

if __name__ == "__main__":
    main()
