import requests
import json
import time

API_URL = "http://127.0.0.1:8000"

def run_e2e_tests():
    print("--- FRAUDSENSE AI FINAL END-TO-END VALIDATION ---")
    
    # Wait for API to be ready
    try:
        resp = requests.get(f"{API_URL}/readiness")
        if resp.status_code != 200:
            print(f"API NOT READY: {resp.text}")
            return
        print("1. Readiness Probe: PASS")
    except Exception as e:
        print(f"API Connection Failed: {e}")
        return

    # Scenario 1: Legitimate Transaction
    payload_legit = {
        "transaction_id": "E2E_LEGIT_1",
        "channel": "NET_BANKING",
        "step": 1,
        "type": "PAYMENT",
        "amount": 100.0,
        "oldbalanceOrg": 5000.0,
        "oldbalanceDest": 0.0
    }
    
    resp_legit = requests.post(f"{API_URL}/predict", json=payload_legit)
    assert resp_legit.status_code == 200
    res_legit = resp_legit.json()
    assert res_legit["recommended_action"] == "APPROVE"
    print("2. Legitimate Transaction (APPROVE): PASS")
    
    # Scenario 2: High-Risk Transaction (Case Generation)
    payload_fraud = {
        "transaction_id": "E2E_FRAUD_1",
        "channel": "UPI",
        "step": 1,
        "type": "TRANSFER",
        "amount": 1500000.0,
        "oldbalanceOrg": 1500000.0,
        "oldbalanceDest": 0.0
    }
    
    resp_fraud = requests.post(f"{API_URL}/predict", json=payload_fraud)
    assert resp_fraud.status_code == 200
    res_fraud = resp_fraud.json()
    assert res_fraud["recommended_action"] in ["BLOCK", "VERIFY"]
    case_id = res_fraud["case_id"]
    assert case_id is not None
    print(f"3. High-Risk Transaction ({res_fraud['recommended_action']}) & Case Generation: PASS")
    
    # Scenario 3: Case Management (Resolve Case)
    time.sleep(1) # Wait for db commit
    
    # First transition to UNDER_REVIEW
    patch_payload_review = {
        "status": "UNDER_REVIEW",
        "analyst_id": "e2e_tester",
        "notes": "Taking ownership."
    }
    resp_review = requests.patch(f"{API_URL}/cases/{case_id}/status", json=patch_payload_review)
    assert resp_review.status_code == 200, f"Failed to set UNDER_REVIEW: {resp_review.text}"

    # Then transition to RESOLVED
    patch_payload_resolve = {
        "status": "RESOLVED",
        "resolution": "CONFIRMED_FRAUD",
        "notes": "E2E Test Resolution",
        "analyst_id": "e2e_tester"
    }
    resp_case = requests.patch(f"{API_URL}/cases/{case_id}/status", json=patch_payload_resolve)
    assert resp_case.status_code == 200, f"Failed to resolve: {resp_case.text}"
    print("4. Case Management (Resolve to CONFIRMED_FRAUD): PASS")
    
    # Scenario 4: Model Monitoring Performance API
    resp_perf = requests.get(f"{API_URL}/monitoring/performance")
    assert resp_perf.status_code == 200
    perf_data = resp_perf.json()
    assert "metrics" in perf_data or perf_data["status"] == "INSUFFICIENT_LABELLED_DATA"
    print("5. Live Performance Monitoring Endpoint: PASS")
    
    # Scenario 5: Explanability
    resp_exp = requests.post(f"{API_URL}/explain", json=payload_fraud)
    assert resp_exp.status_code == 200
    exp_data = resp_exp.json()
    assert len(exp_data["top_factors"]) > 0
    print("6. SHAP Explanability Endpoint: PASS")
    
    print("ALL SCENARIOS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    run_e2e_tests()
