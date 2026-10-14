import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

# Backwards-compatibility shim for preprocessors serialized with scikit-learn < 1.7
try:
    import sklearn.compose._column_transformer as _sct
    if not hasattr(_sct, '_RemainderColsList'):
        class _RemainderColsList(list):
            pass
        _sct._RemainderColsList = _RemainderColsList
except Exception:
    pass

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class DomainRiskEngine:
    """
    Common Risk Engine that routes inputs to domain-specific ML models.
    Supports UPI, Mobile Money, and future domains (Card, Bank, URL, SMS, etc.).
    """
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._preprocessors: Dict[str, Any] = {}
        self._thresholds: Dict[str, float] = {}
        self._schemas: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._initialized = False
        self.load_models()

    def load_models(self):
        registry_path = os.path.join(ROOT_DIR, "models", "model_registry.json")
        if not os.path.exists(registry_path):
            logger.warning("Model registry not found at %s", registry_path)
            return

        try:
            with open(registry_path, "r") as f:
                reg = json.load(f)
                
            domains = reg.get("domains", {})
            for domain_key, info in domains.items():
                model_path = os.path.join(ROOT_DIR, info.get("model_path", ""))
                preprocessor_path = os.path.join(ROOT_DIR, info.get("preprocessor_path", ""))
                threshold_rel = info.get("threshold_path")
                threshold_path = os.path.join(ROOT_DIR, threshold_rel) if threshold_rel else None

                schema_rel = info.get("schema_path")
                schema_path = os.path.join(ROOT_DIR, schema_rel) if schema_rel else None

                metadata_rel = info.get("metadata_path")
                metadata_path = os.path.join(ROOT_DIR, metadata_rel) if metadata_rel else None
                
                if os.path.isfile(model_path) and os.path.isfile(preprocessor_path):
                    try:
                        if model_path.endswith(".joblib"):
                            self._models[domain_key] = joblib.load(model_path)
                        elif model_path.endswith(".json"):
                            import xgboost as xgb
                            clf = xgb.XGBClassifier()
                            clf.load_model(model_path)
                            self._models[domain_key] = clf
                        else:
                            self._models[domain_key] = joblib.load(model_path)
                            
                        self._preprocessors[domain_key] = joblib.load(preprocessor_path)
                        
                        # Load optional isolation forest (UPI domain anomaly augmentation)
                        iso_path = os.path.join(ROOT_DIR, os.path.dirname(info.get("model_path", "")), "isolation_forest.joblib")
                        if os.path.isfile(iso_path):
                            if not hasattr(self, '_isolation_forests'):
                                self._isolation_forests = {}
                            self._isolation_forests[domain_key] = joblib.load(iso_path)
                        
                        # Load threshold
                        if threshold_path and os.path.isfile(threshold_path):
                            with open(threshold_path, "r") as tf:
                                t_data = json.load(tf)
                                self._thresholds[domain_key] = float(t_data.get("optimal_threshold", 0.50))
                        else:
                            self._thresholds[domain_key] = 0.50
                            
                        # Load schema
                        if schema_path and os.path.isfile(schema_path):
                            with open(schema_path, "r") as sf:
                                self._schemas[domain_key] = json.load(sf)
                                
                        # Load metadata
                        if metadata_path and os.path.isfile(metadata_path):
                            with open(metadata_path, "r") as mf:
                                self._metadata[domain_key] = json.load(mf)
                                
                        logger.info("Successfully loaded domain model: %s", domain_key)
                    except Exception as e:
                        logger.error("Failed loading model for domain %s: %s", domain_key, e)
                        
            self._initialized = True
        except Exception as e:
            logger.error("Error reading model registry: %s", e)

    def is_domain_available(self, domain: str) -> bool:
        return domain.lower() in self._models

    def predict_upi(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized inference for UPI payment transactions.
        Includes IsolationForest anomaly score augmentation.
        """
        domain_key = "upi"
        if domain_key not in self._models:
            raise RuntimeError("UPI model is not loaded in risk engine.")

        model = self._models[domain_key]
        preprocessor = self._preprocessors[domain_key]
        threshold = self._thresholds.get(domain_key, 0.50)
        iso = getattr(self, '_isolation_forests', {}).get(domain_key, None)

        # Standard defaults for UPI
        amount = float(payload.get("amount (INR)", payload.get("amount", 0.0)))
        hour = int(payload.get("hour_of_day", 12))
        day = str(payload.get("day_of_week", "Monday"))
        is_wknd = int(payload.get("is_weekend", 1 if day in ["Saturday", "Sunday"] else 0))
        sender_bank = str(payload.get("sender_bank", "HDFC"))
        receiver_bank = str(payload.get("receiver_bank", "SBI"))
        sender_age = str(payload.get("sender_age_group", "26-35"))
        receiver_age = str(payload.get("receiver_age_group", "26-35"))

        # Hour bucket
        if hour <= 5:
            hour_bucket = "late_night"
        elif hour <= 11:
            hour_bucket = "morning"
        elif hour <= 17:
            hour_bucket = "afternoon"
        elif hour <= 22:
            hour_bucket = "evening"
        else:
            hour_bucket = "night"

        # Amount bucket
        if amount <= 500:
            amount_bucket = "very_low"
        elif amount <= 2000:
            amount_bucket = "low"
        elif amount <= 10000:
            amount_bucket = "medium"
        elif amount <= 50000:
            amount_bucket = "high"
        else:
            amount_bucket = "very_high"

        df = pd.DataFrame([{
            "amount (INR)": amount,
            "log_amount": np.log1p(amount),
            "hour_of_day": hour,
            "is_weekend": is_wknd,
            "is_night": 1 if (hour < 6 or hour >= 23) else 0,
            "is_intrabank": 1 if sender_bank == receiver_bank else 0,
            "is_same_age_group": 1 if sender_age == receiver_age else 0,
            "transaction type": str(payload.get("transaction type", payload.get("type", "P2P"))),
            "merchant_category": str(payload.get("merchant_category", "Shopping")),
            "sender_age_group": sender_age,
            "receiver_age_group": receiver_age,
            "sender_state": str(payload.get("sender_state", "Maharashtra")),
            "sender_bank": sender_bank,
            "receiver_bank": receiver_bank,
            "device_type": str(payload.get("device_type", "Android")),
            "network_type": str(payload.get("network_type", "4G")),
            "day_of_week": day,
            "hour_bucket": hour_bucket,
            "amount_bucket": amount_bucket
        }])

        X_proc = preprocessor.transform(df)

        # Augment with IsolationForest anomaly score if available
        if iso is not None:
            anomaly_score = iso.decision_function(X_proc).reshape(-1, 1)
            X_proc = np.hstack([X_proc, anomaly_score])

        prob = float(model.predict_proba(X_proc)[0][1])
        prediction = 1 if prob >= threshold else 0
        risk_score = int(round(prob * 100))

        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        explanations = []
        if amount > 5000:
            explanations.append(f"Elevated transaction amount: INR {amount:,.2f}")
        if hour < 6 or hour >= 23:
            explanations.append(f"High-risk execution window: {hour:02d}:00 hrs")
        if iso is not None and anomaly_score[0][0] < 0:
            explanations.append("Anomalous transaction pattern detected by IsolationForest")

        return {
            "model": "upi_fraud_detector",
            "domain": "UPI",
            "prediction": prediction,
            "label": "FRAUD" if prediction == 1 else "LEGITIMATE",
            "fraud_probability": round(prob, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "threshold": threshold,
            "explanations": explanations
        }

    def predict_card(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized inference for Credit/Debit Card transactions.
        """
        domain_key = "card"
        if domain_key not in self._models:
            raise RuntimeError("Credit Card model is not loaded in risk engine.")

        model = self._models[domain_key]
        preprocessor = self._preprocessors[domain_key]
        threshold = self._thresholds.get(domain_key, 0.95)

        amount = float(payload.get("Amount", payload.get("amount", 0.0)))
        time_val = float(payload.get("Time", payload.get("time", 0.0)))
        hour = int(((time_val // 3600) % 24))

        row_dict = {
            "Time": time_val,
            "Amount": amount,
            "log_amount": np.log1p(amount),
            "hour_of_day": hour,
            "is_night": 1 if hour < 6 else 0
        }
        for i in range(1, 29):
            col_name = f"V{i}"
            row_dict[col_name] = float(payload.get(col_name, 0.0))

        df = pd.DataFrame([row_dict])
        X_proc = preprocessor.transform(df)
        prob = float(model.predict_proba(X_proc)[0][1])
        prediction = 1 if prob >= threshold else 0
        risk_score = int(round(prob * 100))

        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        explanations = []
        if amount > 1000:
            explanations.append(f"Elevated card transaction amount: ${amount:,.2f}")
        if row_dict["V14"] < -2.0:
            explanations.append(f"High-risk latent component deviation on V14 ({row_dict['V14']:.2f})")
        if row_dict["V4"] > 2.0:
            explanations.append(f"High-risk latent component deviation on V4 ({row_dict['V4']:.2f})")

        return {
            "model": "credit_card_fraud_detector",
            "domain": "CARD",
            "prediction": prediction,
            "label": "FRAUD" if prediction == 1 else "LEGITIMATE",
            "fraud_probability": round(prob, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "threshold": threshold,
            "explanations": explanations
        }

    def predict_url(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized inference for URL Phishing detection.
        Supports both pre-extracted feature dictionaries and raw URL strings.
        """
        domain_key = "url_phishing"
        if domain_key not in self._models:
            raise RuntimeError("URL Phishing model is not loaded in risk engine.")

        model = self._models[domain_key]
        preprocessor = self._preprocessors[domain_key]
        threshold = self._thresholds.get(domain_key, 0.40)
        schema = self._schemas.get(domain_key, {})
        required_features = schema.get("required_features", [])

        raw_url = str(payload.get("url", payload.get("URL", "")))
        row_dict = {}

        if raw_url:
            import urllib.parse, ipaddress
            parsed = urllib.parse.urlparse(raw_url if raw_url.startswith(("http://", "https://")) else "https://" + raw_url)
            netloc = parsed.netloc or parsed.path.split("/")[0]
            is_ip = 0
            try:
                ipaddress.ip_address(netloc)
                is_ip = 1
            except ValueError:
                pass
            
            url_len = len(raw_url)
            letters = sum(c.isalpha() for c in raw_url)
            digits = sum(c.isdigit() for c in raw_url)
            special = sum(not c.isalnum() for c in raw_url)

            import re as _re2
            # Compute URLSimilarityIndex — low if domain contains phishing keyword combos
            sim_index = 100
            phishing_kw = ["bank", "secure", "update", "verify", "login", "account", "signin", "credential"]
            kw_hits = sum(1 for kw in phishing_kw if kw in netloc.lower() or kw in (parsed.path or "").lower())
            has_hyphen_compound = bool(_re2.search(r'[a-z]+-[a-z]+-(login|update|secure|verify|bank)', netloc.lower()))
            for brand in ["paypal", "chase", "apple", "google", "bank", "crypto"]:
                if brand in netloc.lower() and not netloc.lower().endswith(f"{brand}.com"):
                    sim_index = 0
            if kw_hits >= 2:
                sim_index = min(sim_index, max(0, 30 - (kw_hits * 8)))
            if has_hyphen_compound:
                sim_index = min(sim_index, 15)

            # TLD risk scoring — suspicious TLDs known for phishing campaigns
            suspicious_tlds = {"top", "xyz", "gq", "tk", "ml", "cf", "ga", "pw", "zip", "review", "country", "kim", "bid", "stream"}
            tld = netloc.split(".")[-1].lower() if "." in netloc else ""
            tld_legit_prob = 0.05 if tld in suspicious_tlds else (0.1 if is_ip else 0.6)

            row_dict = {
                "_domain_str": netloc.lower() + (parsed.path or "").lower(),  # private key for heuristic
                "URLLength": url_len,
                "DomainLength": len(netloc),
                "IsDomainIP": is_ip,
                "URLSimilarityIndex": sim_index,
                "CharContinuationRate": 0.5,
                "TLDLegitimateProb": tld_legit_prob,
                "URLCharProb": float(letters / max(1, url_len)),
                "TLDLength": len(tld) if tld else 3,
                "NoOfSubDomain": max(0, netloc.count(".") - 1),
                "HasObfuscation": 1 if "%" in raw_url else 0,
                "NoOfLettersInURL": letters,
                "LetterRatioInURL": float(letters / max(1, url_len)),
                "NoOfDegitsInURL": digits,
                "DegitRatioInURL": float(digits / max(1, url_len)),
                "NoOfEqualsInURL": raw_url.count("="),
                "NoOfQMarkInURL": raw_url.count("?"),
                "NoOfAmpersandInURL": raw_url.count("&"),
                "NoOfOtherSpecialCharsInURL": special,
                "SpacialCharRatioInURL": float(special / max(1, url_len)),
                "IsHTTPS": 1 if raw_url.startswith("https") else 0,
                "Bank": 1 if any(b in raw_url.lower() for b in ["bank", "chase", "wellsfargo"]) else 0,
                "Pay": 1 if any(p in raw_url.lower() for p in ["pay", "paypal", "stripe"]) else 0,
                "Crypto": 1 if any(c in raw_url.lower() for c in ["crypto", "btc", "eth", "binance"]) else 0,
            }

        for feat in required_features:
            if feat in payload:
                row_dict[feat] = float(payload[feat])
            elif feat not in row_dict:
                # Use legitimate-site medians as defaults for DOM features not available from URL-only analysis.
                # This prevents false-positives on real sites: zeroed DOM features match the phishing cluster.
                # Medians are derived from the PhiUSIIL training data (legit class, label=1).
                LEGIT_DOM_DEFAULTS = {
                    "HasTitle": 1.0,
                    "HasFavicon": 1.0,
                    "IsResponsive": 1.0,
                    "HasDescription": 1.0,
                    "HasCopyrightInfo": 1.0,
                    "NoOfImage": 25.0,
                    "NoOfCSS": 6.0,
                    "NoOfJS": 14.0,
                    "NoOfSelfRef": 76.0,
                    "LineOfCode": 1105.0,
                    "LargestLineLength": 400.0,
                    "HasSubmitButton": 0.0,
                    "HasPasswordField": 0.0,
                    "HasExternalFormSubmit": 0.0,
                    "HasHiddenFields": 0.0,
                    "NoOfPopup": 0.0,
                    "NoOfiFrame": 0.0,
                    "Robots": 1.0,
                    "HasSocialNet": 0.0,
                    "NoOfURLRedirect": 0.0,
                    "NoOfSelfRedirect": 0.0,
                    "NoOfEmptyRef": 0.0,
                    "NoOfExternalRef": 10.0,
                    "DomainTitleMatchScore": 80.0,
                    "URLTitleMatchScore": 60.0,
                    "ObfuscationRatio": 0.0,
                    "NoOfObfuscatedChar": 0.0,
                    "CharContinuationRate": 0.5,
                }
                row_dict[feat] = LEGIT_DOM_DEFAULTS.get(feat, 0.0)

        df = pd.DataFrame([[row_dict[feat] for feat in required_features]], columns=required_features)
        X_proc = preprocessor.transform(df)
        proba_all = model.predict_proba(X_proc)[0]

        # Dataset label encoding: 0 = PHISHING, 1 = LEGITIMATE
        # model.classes_ = [0, 1], so proba_all[0] = P(phishing), proba_all[1] = P(legitimate)
        classes = list(model.classes_)
        phishing_class_idx = classes.index(0) if 0 in classes else 0
        prob = float(proba_all[phishing_class_idx])  # phishing probability

        # Heuristic boost: only apply when TLD is suspicious (not trusted .com/.org/.net/.edu/.gov)
        # This prevents false-positives on legitimate sites that happen to contain banking keywords (e.g. southbankmosaics.com)
        import re as _re
        TRUSTED_TLDS = {"com", "org", "net", "edu", "gov", "co", "io", "uk", "de", "fr", "au", "jp", "in"}
        domain_lower = row_dict.get("_domain_str", "") or ""
        tld_from_domain = domain_lower.split(".")[-1].split("/")[0] if "." in domain_lower else ""
        is_trusted_tld = tld_from_domain in TRUSTED_TLDS
        phishing_domain_signals = [
            bool(_re.search(r'(bank|secure|update|verify|login|account|signin|credential)', domain_lower)),
            bool(_re.search(r'-(update|secure|login|verify|bank)', domain_lower)),
            row_dict.get("URLSimilarityIndex", 100) < 30,
            row_dict.get("NoOfSubDomain", 0) >= 3,
            row_dict.get("HasObfuscation", 0) == 1,
        ]
        heuristic_signal_count = sum(1 for s in phishing_domain_signals if s)
        # Only boost if TLD itself is suspicious — avoids false-positives on legit .com sites
        if not is_trusted_tld and heuristic_signal_count >= 2:
            heuristic_boost = min(heuristic_signal_count * 0.18, 0.72)
            prob = max(prob, heuristic_boost)
        else:
            heuristic_boost = 0.0

        threshold = self._thresholds.get(domain_key, 0.35)
        prediction = 1 if prob >= threshold else 0
        risk_score = int(round(prob * 100))

        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 35:
            risk_level = "SUSPICIOUS"
        else:
            risk_level = "LOW"

        explanations = []
        if row_dict.get("IsDomainIP") == 1:
            explanations.append("URL hostname contains raw IP address — high-risk indicator.")
        if row_dict.get("IsHTTPS") == 0:
            explanations.append("Unencrypted HTTP connection — susceptible to interception.")
        if row_dict.get("NoOfDegitsInURL", 0) > 10:
            explanations.append("Suspiciously high digit count in URL.")
        if row_dict.get("HasObfuscation") == 1:
            explanations.append("Obfuscated or percent-encoded characters detected in URL.")
        if row_dict.get("URLSimilarityIndex", 100) < 30:
            explanations.append("Domain similarity to known brands is very low — possible typosquat.")
        if heuristic_signal_count >= 2:
            explanations.append(
                f"Domain contains {heuristic_signal_count} high-risk keyword/structural signals "
                "(e.g., 'bank', 'update', 'secure', 'login' combined with non-standard TLD or hyphenation)."
            )

        return {
            "model": "url_phishing_detector",
            "domain": "URL_PHISHING",
            "prediction": prediction,
            "label": "PHISHING" if prediction == 1 else "LEGITIMATE",
            "fraud_probability": round(prob, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "threshold": threshold,
            "explanations": explanations
        }

    def predict_sms(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized inference for SMS Scam / Spam text classification.
        """
        domain_key = "sms"
        if domain_key not in self._models:
            raise RuntimeError("SMS Scam model is not loaded in risk engine.")

        model = self._models[domain_key]
        bundle = self._preprocessors[domain_key]
        threshold = self._thresholds.get(domain_key, 0.40)
        
        vectorizer = bundle["vectorizer"]
        scaler = bundle["scaler"]

        raw_text = str(payload.get("text", payload.get("message", "")))
        if not raw_text:
            return {
                "model": "sms_spam_detector",
                "domain": "SMS",
                "prediction": 0,
                "label": "HAM_LEGITIMATE",
                "fraud_probability": 0.0,
                "risk_score": 0,
                "risk_level": "LOW",
                "threshold": threshold,
                "explanations": ["Empty text payload."]
            }

        import re
        from scipy.sparse import hstack
        URL_RE = re.compile(r'https?://\S+|www\.\S+|bit\.ly/\S+|tinyurl\.com/\S+', re.IGNORECASE)
        PHONE_RE = re.compile(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}|\b\d{5,12}\b')
        CURRENCY_RE = re.compile(r'[$£€₹]|rs\.?|inr|cash|prize|reward|free|won|win', re.IGNORECASE)

        t_len = max(1, len(raw_text))
        meta_dict = {
            "char_length": len(raw_text),
            "word_count": len(raw_text.split()),
            "has_url": 1 if URL_RE.search(raw_text) else 0,
            "has_phone": 1 if PHONE_RE.search(raw_text) else 0,
            "has_currency": 1 if CURRENCY_RE.search(raw_text) else 0,
            "upper_ratio": float(sum(1 for c in raw_text if c.isupper()) / t_len),
            "digit_ratio": float(sum(1 for c in raw_text if c.isdigit()) / t_len),
            "exclamation_count": raw_text.count('!'),
            "question_count": raw_text.count('?')
        }
        meta_df = pd.DataFrame([meta_dict])

        X_tfidf = vectorizer.transform([raw_text])
        X_meta = scaler.transform(meta_df)
        X_proc = hstack([X_tfidf, X_meta]).tocsr()

        prob = float(model.predict_proba(X_proc)[0][1])
        prediction = 1 if prob >= threshold else 0
        risk_score = int(round(prob * 100))

        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        explanations = []
        if meta_dict["has_url"] == 1:
            explanations.append("SMS contains embedded hyperlink or shortened URL.")
        if meta_dict["has_currency"] == 1:
            explanations.append("Suspicious financial promise or currency indicator.")
        if meta_dict["has_phone"] == 1:
            explanations.append("Embedded callback telephone or shortcode number.")
        if meta_dict["upper_ratio"] > 0.20:
            explanations.append("Elevated uppercase urgent formatting.")

        return {
            "model": "sms_spam_detector",
            "domain": "SMS",
            "prediction": prediction,
            "label": "SPAM_SCAM" if prediction == 1 else "HAM_LEGITIMATE",
            "fraud_probability": round(prob, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "threshold": threshold,
            "explanations": explanations
        }

    def predict_bank(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized inference for Bank Account Fraud detection.
        Expects behavioral, velocity, device and identity features.
        """
        domain_key = "bank"
        if domain_key not in self._models:
            raise RuntimeError("Bank model is not loaded in risk engine.")

        model = self._models[domain_key]
        preprocessor = self._preprocessors[domain_key]
        threshold = self._thresholds.get(domain_key, 0.90)

        # Extract fields with sensible defaults
        income = float(payload.get("income", 0.5))
        name_email_sim = float(payload.get("name_email_similarity", 0.5))
        prev_addr = int(payload.get("prev_address_months_count", -1))
        curr_addr = int(payload.get("current_address_months_count", 24))
        customer_age = int(payload.get("customer_age", 35))
        days_since_req = float(payload.get("days_since_request", 0.0))
        intended_amount = float(payload.get("intended_balcon_amount", 0.0))
        payment_type = str(payload.get("payment_type", "AB"))
        zip_count = int(payload.get("zip_count_4w", 100))
        vel_6h = float(payload.get("velocity_6h", 5000.0))
        vel_24h = float(payload.get("velocity_24h", 5000.0))
        vel_4w = float(payload.get("velocity_4w", 6000.0))
        branch_count = int(payload.get("bank_branch_count_8w", 5))
        dob_emails = int(payload.get("date_of_birth_distinct_emails_4w", 5))
        employment = str(payload.get("employment_status", "CA"))
        credit_score = int(payload.get("credit_risk_score", 100))
        email_free = int(payload.get("email_is_free", 1))
        housing = str(payload.get("housing_status", "BC"))
        phone_home = int(payload.get("phone_home_valid", 0))
        phone_mobile = int(payload.get("phone_mobile_valid", 1))
        bank_months = int(payload.get("bank_months_count", 12))
        other_cards = int(payload.get("has_other_cards", 0))
        credit_limit = float(payload.get("proposed_credit_limit", 1500.0))
        foreign = int(payload.get("foreign_request", 0))
        source = str(payload.get("source", "INTERNET"))
        session_len = float(payload.get("session_length_in_minutes", 10.0))
        device_os = str(payload.get("device_os", "windows"))
        keep_alive = int(payload.get("keep_alive_session", 1))
        device_emails = int(payload.get("device_distinct_emails_8w", 1))
        device_fraud = int(payload.get("device_fraud_count", 0))
        month = int(payload.get("month", 0))

        # Engineered features (must match training)
        vel_ratio_6h_24h = vel_6h / (vel_24h + 1e-6)
        vel_ratio_24h_4w = vel_24h / (vel_4w + 1e-6)
        identity_anomaly = (1 - name_email_sim) + email_free + (1 - phone_home) + (1 - phone_mobile)
        if credit_score <= 0:
            credit_risk_bucket = "negative"
        elif credit_score <= 50:
            credit_risk_bucket = "very_poor"
        elif credit_score <= 100:
            credit_risk_bucket = "poor"
        elif credit_score <= 200:
            credit_risk_bucket = "fair"
        else:
            credit_risk_bucket = "good"
        is_new_address = 1 if curr_addr < 6 else 0
        has_unknown_prev = 1 if prev_addr == -1 else 0
        is_high_vel = 1 if vel_6h > 12000 else 0  # approximate 95th pct
        device_reuse = 1 if device_emails > 1 else 0

        row = {
            "income": income,
            "name_email_similarity": name_email_sim,
            "prev_address_months_count": prev_addr,
            "current_address_months_count": curr_addr,
            "customer_age": customer_age,
            "days_since_request": days_since_req,
            "intended_balcon_amount": intended_amount,
            "payment_type": payment_type,
            "zip_count_4w": zip_count,
            "velocity_6h": vel_6h,
            "velocity_24h": vel_24h,
            "velocity_4w": vel_4w,
            "bank_branch_count_8w": branch_count,
            "date_of_birth_distinct_emails_4w": dob_emails,
            "employment_status": employment,
            "credit_risk_score": credit_score,
            "email_is_free": email_free,
            "housing_status": housing,
            "phone_home_valid": phone_home,
            "phone_mobile_valid": phone_mobile,
            "bank_months_count": bank_months,
            "has_other_cards": other_cards,
            "proposed_credit_limit": credit_limit,
            "foreign_request": foreign,
            "source": source,
            "session_length_in_minutes": session_len,
            "device_os": device_os,
            "keep_alive_session": keep_alive,
            "device_distinct_emails_8w": device_emails,
            "device_fraud_count": device_fraud,
            "month": month,
            # Engineered
            "velocity_ratio_6h_24h": vel_ratio_6h_24h,
            "velocity_ratio_24h_4w": vel_ratio_24h_4w,
            "identity_anomaly_score": identity_anomaly,
            "credit_risk_bucket": credit_risk_bucket,
            "is_new_address": is_new_address,
            "has_unknown_prev_address": has_unknown_prev,
            "is_high_velocity": is_high_vel,
            "device_reuse_risk": device_reuse,
            "log_velocity_6h": np.log1p(max(0, vel_6h)),
            "log_velocity_24h": np.log1p(max(0, vel_24h)),
            "log_velocity_4w": np.log1p(max(0, vel_4w)),
            "log_zip_count_4w": np.log1p(max(0, zip_count)),
            "log_session_length_in_minutes": np.log1p(max(0, session_len))
        }

        df = pd.DataFrame([row])
        X_proc = preprocessor.transform(df)
        prob = float(model.predict_proba(X_proc)[0][1])
        prediction = 1 if prob >= threshold else 0
        risk_score = int(round(prob * 100))

        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        explanations = []
        if foreign:
            explanations.append("Request originated from a foreign IP address.")
        if is_new_address:
            explanations.append("Very recent address change (< 6 months).")
        if has_unknown_prev:
            explanations.append("No prior address history on record.")
        if device_fraud > 0:
            explanations.append(f"Device has {device_fraud} prior fraud event(s).")
        if device_reuse:
            explanations.append("Multiple distinct email addresses linked to this device.")
        if identity_anomaly > 2:
            explanations.append("Multiple identity inconsistency signals (name/email/phone).")
        if credit_score < 50:
            explanations.append(f"Very poor credit risk score: {credit_score}.")

        return {
            "model": "bank_fraud_detector",
            "domain": "BANK",
            "prediction": prediction,
            "label": "FRAUD" if prediction == 1 else "LEGITIMATE",
            "fraud_probability": round(prob, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "threshold": threshold,
            "explanations": explanations
        }

    def predict_paysim(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized inference for PaySim Mobile Money Fraud.
        """
        domain_key = "paysim"
        if domain_key not in self._models:
            raise RuntimeError("PaySim model is not loaded in risk engine.")

        model = self._models[domain_key]
        preprocessor = self._preprocessors[domain_key]
        threshold = self._thresholds.get(domain_key, 0.525)

        step = int(payload.get("step", 1))
        tx_type = str(payload.get("type", "TRANSFER")).upper()
        amount = float(payload.get("amount", 0.0))
        oldbalanceOrg = float(payload.get("oldbalanceOrg", 0.0))
        newbalanceOrig = float(payload.get("newbalanceOrig", 0.0))
        oldbalanceDest = float(payload.get("oldbalanceDest", 0.0))
        newbalanceDest = float(payload.get("newbalanceDest", 0.0))

        # Only TRANSFER and CASH_OUT can be fraudulent in PaySim
        if tx_type not in ["TRANSFER", "CASH_OUT"]:
            return {
                "model": "paysim_fraud_detector",
                "domain": "MOBILE_MONEY_PAYSIM",
                "prediction": 0,
                "label": "LEGITIMATE",
                "fraud_probability": 0.0,
                "risk_score": 0,
                "risk_level": "LOW",
                "threshold": threshold,
                "explanations": [f"Transaction type {tx_type} is not associated with fraud patterns."]
            }

        # Engineer features
        balance_error_orig = newbalanceOrig - (oldbalanceOrg - amount)
        balance_error_dest = newbalanceDest - (oldbalanceDest + amount)
        orig_drained_to_zero = 1 if (oldbalanceOrg > 0 and newbalanceOrig == 0) else 0
        dest_no_change = 1 if (oldbalanceDest == newbalanceDest and amount > 0) else 0
        amount_ratio_orig = amount / (oldbalanceOrg + 1.0)
        log_amount = np.log1p(amount)
        log_oldbalanceOrg = np.log1p(oldbalanceOrg)
        log_oldbalanceDest = np.log1p(oldbalanceDest)
        is_unusual_hour = 1 if (step % 24) < 6 else 0

        row = {
            "step": step,
            "type": tx_type,
            "amount": amount,
            "oldbalanceOrg": oldbalanceOrg,
            "newbalanceOrig": newbalanceOrig,
            "oldbalanceDest": oldbalanceDest,
            "newbalanceDest": newbalanceDest,
            "balance_error_orig": balance_error_orig,
            "balance_error_dest": balance_error_dest,
            "orig_drained_to_zero": orig_drained_to_zero,
            "dest_no_change": dest_no_change,
            "amount_ratio_orig": amount_ratio_orig,
            "log_amount": log_amount,
            "log_oldbalanceOrg": log_oldbalanceOrg,
            "log_oldbalanceDest": log_oldbalanceDest,
            "is_unusual_hour": is_unusual_hour
        }

        df = pd.DataFrame([row])
        X_proc = preprocessor.transform(df)
        prob = float(model.predict_proba(X_proc)[0][1])
        prediction = 1 if prob >= threshold else 0
        risk_score = int(round(prob * 100))

        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        explanations = []
        if orig_drained_to_zero:
            explanations.append("Origin account drained entirely to zero.")
        if dest_no_change and tx_type == "TRANSFER":
            explanations.append("Transferred amount did not appear in destination account.")
        if amount_ratio_orig >= 1.0:
            explanations.append("Transaction amount meets or exceeds entire origin balance.")
        if is_unusual_hour:
            explanations.append("Transaction occurred during unusual late-night hours.")

        return {
            "model": "paysim_fraud_detector",
            "domain": "MOBILE_MONEY_PAYSIM",
            "prediction": prediction,
            "label": "FRAUD" if prediction == 1 else "LEGITIMATE",
            "fraud_probability": round(prob, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "threshold": threshold,
            "explanations": explanations
        }

    def predict_bitcoin(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized inference for Elliptic Bitcoin Illicit Transactions.
        Expects 165 numerical features.
        """
        domain_key = "bitcoin"
        if domain_key not in self._models:
            raise RuntimeError("Bitcoin model is not loaded in risk engine.")

        model = self._models[domain_key]
        preprocessor = self._preprocessors[domain_key]
        threshold = self._thresholds.get(domain_key, 0.825)
        schema = self._schemas.get(domain_key, {})
        required_features = schema.get("required_raw_features", [f"feature_{i}" for i in range(1, 166)])

        row = {}
        for feat in required_features:
            row[feat] = float(payload.get(feat, 0.0))

        df = pd.DataFrame([row])
        X_proc = preprocessor.transform(df)
        prob = float(model.predict_proba(X_proc)[0][1])
        prediction = 1 if prob >= threshold else 0
        risk_score = int(round(prob * 100))

        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        explanations = []
        if risk_score >= 75:
            explanations.append("High probability of illicit activity based on transaction graph features.")

        return {
            "model": "bitcoin_fraud_detector",
            "domain": "CRYPTO_BITCOIN",
            "prediction": prediction,
            "label": "ILLICIT_FRAUD" if prediction == 1 else "LICIT",
            "fraud_probability": round(prob, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "threshold": threshold,
            "explanations": explanations
        }

    def predict_email(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized inference for Email Phishing text classification.
        """
        domain_key = "email"
        if domain_key not in self._models:
            raise RuntimeError("Email Phishing model is not loaded in risk engine.")

        model = self._models[domain_key]
        bundle = self._preprocessors[domain_key]
        threshold = self._thresholds.get(domain_key, 0.40)

        vectorizer = bundle["vectorizer"]
        scaler = bundle["scaler"]

        raw_text = str(payload.get("text", payload.get("body", payload.get("subject", ""))))
        if not raw_text:
            return {
                "model": "email_phishing_detector",
                "domain": "EMAIL",
                "prediction": 0,
                "label": "HAM_LEGITIMATE",
                "fraud_probability": 0.0,
                "risk_score": 0,
                "risk_level": "LOW",
                "threshold": threshold,
                "explanations": ["Empty email text payload."]
            }

        import re
        from scipy.sparse import hstack
        URL_REGEX = re.compile(r'https?://\S+|www\.\S+|\.com/\S+|\.net/\S+', re.IGNORECASE)
        URGENT_REGEX = re.compile(r'\b(urgent|immediately|suspended|suspend|deactivated|action required|warning|threat|notice)\b', re.IGNORECASE)
        FINANCIAL_REGEX = re.compile(r'\b(invoice|account|bank|payment|wire|transfer|funds|dollars|billing|payroll)\b', re.IGNORECASE)
        CRED_REGEX = re.compile(r'\b(password|login|verify|credential|otp|pin|security code|authenticate|reset)\b', re.IGNORECASE)

        t_len = max(1, len(raw_text))
        meta_dict = {
            "char_length": len(raw_text),
            "word_count": len(raw_text.split()),
            "has_url": 1 if URL_REGEX.search(raw_text) else 0,
            "has_urgent": 1 if URGENT_REGEX.search(raw_text) else 0,
            "has_financial": 1 if FINANCIAL_REGEX.search(raw_text) else 0,
            "has_cred": 1 if CRED_REGEX.search(raw_text) else 0,
            "upper_ratio": float(sum(1 for c in raw_text if c.isupper()) / t_len),
            "digit_ratio": float(sum(1 for c in raw_text if c.isdigit()) / t_len)
        }
        meta_df = pd.DataFrame([meta_dict])

        X_tfidf = vectorizer.transform([raw_text])
        X_meta = scaler.transform(meta_df)
        X_proc = hstack([X_tfidf, X_meta]).tocsr()

        prob = float(model.predict_proba(X_proc)[0][1])
        prediction = 1 if prob >= threshold else 0
        risk_score = int(round(prob * 100))

        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        explanations = []
        if meta_dict["has_urgent"] == 1:
            explanations.append("Urgent or threatening call-to-action detected.")
        if meta_dict["has_cred"] == 1:
            explanations.append("Suspicious credential or verification request.")
        if meta_dict["has_url"] == 1:
            explanations.append("Contains embedded link.")
        if meta_dict["has_financial"] == 1:
            explanations.append("Payment or billing context identified.")

        return {
            "model": "email_phishing_detector",
            "domain": "EMAIL",
            "prediction": prediction,
            "label": "PHISHING" if prediction == 1 else "LEGITIMATE",
            "fraud_probability": round(prob, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "threshold": threshold,
            "explanations": explanations
        }

    def predict(self, domain: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        d = domain.lower()
        if d == "upi":
            return self.predict_upi(input_data)
        elif d in ["card", "credit_card", "creditcard"]:
            return self.predict_card(input_data)
        elif d in ["url", "url_phishing", "phishing_url", "link"]:
            return self.predict_url(input_data)
        elif d in ["sms", "text", "smishing"]:
            return self.predict_sms(input_data)
        elif d in ["email", "email_phishing", "phishing_email"]:
            return self.predict_email(input_data)
        elif d in ["bank", "bank_account", "account_fraud"]:
            return self.predict_bank(input_data)
        elif d in ["paysim", "mobile_money"]:
            return self.predict_paysim(input_data)
        elif d in ["bitcoin", "crypto", "btc"]:
            return self.predict_bitcoin(input_data)
        else:
            raise NotImplementedError(f"Domain '{domain}' router is not yet configured.")

risk_engine = DomainRiskEngine()

