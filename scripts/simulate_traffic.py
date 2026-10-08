import requests
import random
import time
import json
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://localhost:8000/api/v1/predict"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "test-key-123"
}

# Define realistic payloads for various domains
PAYLOADS = [
    {
        "domain": "paysim",
        "step": 1,
        "type": "TRANSFER",
        "amount": 150000.0,
        "oldbalanceOrg": 150000.0,
        "newbalanceOrig": 0.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0
    },
    {
        "domain": "paysim",
        "step": 1,
        "type": "PAYMENT",
        "amount": 200.0,
        "oldbalanceOrg": 5000.0,
        "newbalanceOrig": 4800.0,
        "oldbalanceDest": 1000.0,
        "newbalanceDest": 1200.0
    },
    {
        "domain": "bank",
        "income": 0.5,
        "name_email_similarity": 0.8,
        "velocity_6h": 100,
        "velocity_24h": 200,
        "velocity_4w": 300,
        "bank_branch_count_8w": 5,
        "date_of_birth_distinct_emails_4w": 1,
        "credit_risk_score": 150,
        "email_is_free": 1,
        "phone_home_valid": 1,
        "phone_mobile_valid": 1,
        "bank_months_count": 12,
        "has_other_cards": 0,
        "proposed_credit_limit": 1000,
        "foreign_request": 0,
        "session_length_in_minutes": 5,
        "keep_alive_session": 1,
        "device_os": 0,
        "device_distinct_emails_8w": 1,
        "month": 5
    },
    {
        "domain": "upi",
        "amount": 150.0,
        "merchant_type": 1,
        "is_international": 0,
        "time_of_day": 14,
        "velocity_1h": 2
    },
    {
        "domain": "card",
        "V1": -1.3, "V2": 0.5, "V3": 1.2, "V4": 0.1, "V5": -0.8,
        "V6": 0.3, "V7": 0.1, "V8": 0.2, "V9": 0.5, "V10": 0.9,
        "V11": -0.5, "V12": -1.0, "V13": 0.2, "V14": 0.4, "V15": -0.3,
        "V16": 0.6, "V17": 0.1, "V18": -0.2, "V19": 0.8, "V20": 0.2,
        "V21": -0.1, "V22": 0.3, "V23": -0.4, "V24": 0.2, "V25": 0.1,
        "V26": -0.2, "V27": 0.0, "V28": -0.1, "Amount": 12.50
    },
    {
        "domain": "bitcoin"
    } # Adding dummy bitcoin features dynamically
]

# Add dummy features to bitcoin payload
for i in range(1, 166):
    PAYLOADS[-1][f"feature_{i}"] = random.uniform(-2, 2)


def send_request():
    payload = random.choice(PAYLOADS).copy()
    payload["transaction_id"] = f"TX_SIM_{int(time.time() * 1000)}_{random.randint(100, 999)}"
    
    try:
        start = time.time()
        response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=5)
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            result = response.json()
            domain = payload["domain"].upper()
            pred = result.get("prediction", "UNKNOWN")
            risk = result.get("risk_level", "UNKNOWN")
            print(f"[OK] {domain} | {latency:.1f}ms | Pred: {pred} | Risk: {risk}")
        else:
            print(f"[ERROR] HTTP {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[FAILED] Could not connect to API: {e}")

def main():
    print(f"Starting Multi-Domain API Traffic Simulator -> {API_URL}")
    print("Press Ctrl+C to stop.")
    print("-" * 50)
    
    try:
        while True:
            # Simulate concurrent users
            threads = random.randint(1, 4)
            with ThreadPoolExecutor(max_workers=threads) as executor:
                for _ in range(threads):
                    executor.submit(send_request)
            
            # Random delay between batches
            time.sleep(random.uniform(0.5, 2.0))
    except KeyboardInterrupt:
        print("\nTraffic simulator stopped.")

if __name__ == "__main__":
    main()
