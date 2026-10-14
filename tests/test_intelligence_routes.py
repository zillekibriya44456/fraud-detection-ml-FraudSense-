"""Contract tests for the public fraud-intelligence scanner endpoints."""

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_url_scanner_flags_brand_impersonation_and_credential_path():
    response = client.post(
        "/api/v1/scans/url",
        json={"url": "http://chase-security-check.example/login"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ["HIGH", "CRITICAL"]
    assert data["possible_brand_impersonation"] == "chase"
    assert data["has_ip_host"] is False


def test_url_scanner_rejects_private_network_addresses():
    response = client.post(
        "/api/v1/scans/url",
        json={"url": "http://192.168.1.10/payment"},
    )

    assert response.status_code == 400
    assert "SSRF Protection" in response.json()["detail"]


def test_qr_scanner_flags_suspicious_high_value_upi_request():
    response = client.post(
        "/api/v1/scans/qr",
        json={"payload": "upi://pay?pa=lottery-winner@upi&pn=Prize&am=9000"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["qr_type"] == "UPI"
    assert data["risk_level"] == "HIGH"
    assert data["payee_id"] == "lottery-winner@upi"


def test_qr_scanner_rejects_non_numeric_amount():
    response = client.post("/api/v1/scans/qr", json={"payload": "upi://pay?pa=merchant@upi&am=not-a-number"})
    assert response.status_code == 422


def test_sms_scanner_identifies_kyc_otp_phishing():
    response = client.post(
        "/api/v1/scans/sms",
        json={"text": "Urgent KYC update: share your OTP or account blocked within 24 hours https://evil.example"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["scam_category"] == "FAKE_KYC"
    assert data["risk_level"] == "CRITICAL"
    assert data["urgency_detected"] is True


def test_upi_prediction_endpoint():
    response = client.post(
        "/api/v1/predict/upi",
        json={
            "amount": 7500.0,
            "transaction_type": "P2P",
            "merchant_category": "Shopping",
            "sender_age_group": "26-35",
            "receiver_age_group": "18-25",
            "sender_state": "Maharashtra",
            "sender_bank": "HDFC",
            "receiver_bank": "SBI",
            "device_type": "Android",
            "network_type": "5G",
            "hour_of_day": 23,
            "day_of_week": "Friday"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "UPI"
    assert data["model"] == "upi_fraud_detector"
    assert "prediction" in data
    assert "fraud_probability" in data
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

