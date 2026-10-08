import shap
import pandas as pd
from src.features.realtime_features import engineer_realtime_features

class SHAPExplainer:
    def __init__(self, model, preprocessor):
        self.model = model
        self.preprocessor = preprocessor
        self.explainer = None
        
        if model is not None:
            # TreeExplainer is extremely fast for XGBoost
            self.explainer = shap.TreeExplainer(model)

    def explain_transaction(self, transaction_data: dict) -> list[dict]:
        if not self.explainer:
            return []
            
        safe_keys = ['step', 'type', 'amount', 'oldbalanceOrg', 'oldbalanceDest']
        safe_data = {k: transaction_data.get(k, 0) for k in safe_keys}
        
        df = pd.DataFrame([safe_data])
        df_engineered = engineer_realtime_features(df)
        X_processed = self.preprocessor.transform(df_engineered)
        
        # Get feature names from preprocessor
        numeric_features = ['step', 'amount', 'oldbalanceOrg', 'oldbalanceDest', 'hour_of_day', 'amount_to_balance_ratio', 'emptying_account']
        # Categorical depends on onehot, we'll extract directly if possible
        try:
            cat_features = self.preprocessor.named_transformers_['cat'].named_steps['onehot'].get_feature_names_out(['type'])
            feature_names = numeric_features + list(cat_features)
        except (AttributeError, KeyError):
            feature_names = [f"Feature_{i}" for i in range(X_processed.shape[1])]

        shap_values = self.explainer.shap_values(X_processed)
        
        # XGBoost SHAP might return a list for multiclass or a 2D array for binary.
        if isinstance(shap_values, list):
            shap_values = shap_values[1] # positive class
            
        shap_values_flat = shap_values[0]
        
        impacts = []
        for i, val in enumerate(shap_values_flat):
            if i < len(feature_names):
                impacts.append({"feature": feature_names[i], "impact": float(val)})
                
        # Sort by absolute impact
        impacts.sort(key=lambda x: abs(x["impact"]), reverse=True)
        return impacts[:5] # Return top 5 factors
