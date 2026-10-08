import re
import ipaddress
import urllib.parse
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import TransactionAuditLog

router = APIRouter(prefix="/api/v1", tags=["fraud-intelligence"])

# ------------------------------------------------------------------------------
# 1. UNIVERSAL LINK SCANNER (WITH SSRF PROTECTION)
# ------------------------------------------------------------------------------
class URLScanRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2_048)

class URLScanResponse(BaseModel):
    url: str
    domain: str
    scheme: str
    risk_level: str  # LOW, SUSPICIOUS, HIGH, CRITICAL
    risk_score: float # 0.0 to 1.0
    evidence: List[str]
    warnings: List[str]
    recommendation: str
    is_https: bool
    has_ip_host: bool
    possible_brand_impersonation: Optional[str] = None
    scanned_at: str

BLOCKED_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"), # Cloud metadata
    ipaddress.ip_network("0.0.0.0/8"),
]

KNOWN_BRANDS = ["paypal", "chase", "bankofamerica", "wellsfargo", "binance", "stripe", "razorpay", "paytm", "gpay"]

@router.post("/scans/url", response_model=URLScanResponse)
def scan_url(request: URLScanRequest):
    raw_url = request.url.strip()
    if not raw_url.startswith(("http://", "https://")):
        raw_url = "https://" + raw_url

    parsed = urllib.parse.urlparse(raw_url)
    hostname = parsed.hostname or ""

    if not hostname:
        raise HTTPException(status_code=400, detail="Invalid URL hostname")

    # SSRF Protection Check
    try:
        ip = ipaddress.ip_address(hostname)
        has_ip_host = True
        for blocked_net in BLOCKED_IP_RANGES:
            if ip in blocked_net:
                raise HTTPException(
                    status_code=400, 
                    detail="Security Protection: Access to private or local loopback IP ranges is strictly prohibited (SSRF Protection)."
                )
    except ValueError:
        has_ip_host = False

    evidence = []
    warnings = []
    risk_score = 0.0

    # 1. Protocol check
    is_https = parsed.scheme.lower() == "https"
    if not is_https:
        warnings.append("Unencrypted connection (HTTP). Potential eavesdropping risk.")
        risk_score += 0.25
    else:
        evidence.append("Encrypted HTTPS connection.")

    # 2. IP Host check
    if has_ip_host:
        warnings.append("URL uses a raw IP address instead of a registered domain name.")
        risk_score += 0.35

    # 3. Path & Query Suspicious Keywords
    suspicious_keywords = ["login", "verify", "secure", "update", "account", "banking", "wallet", "otp", "password", "confirm", "claim", "reward", "free"]
    matched_kw = [kw for kw in suspicious_keywords if kw in parsed.path.lower() or kw in parsed.query.lower()]
    if matched_kw:
        warnings.append(f"Suspicious security/credential keywords detected in URL path: {', '.join(matched_kw)}")
        risk_score += 0.20 * min(len(matched_kw), 3)

    # 4. Brand Impersonation / Typosquatting Check
    domain = hostname.lower()
    impersonated_brand = None
    for brand in KNOWN_BRANDS:
        if brand in domain and not domain.endswith(f".{brand}.com") and domain != f"{brand}.com" and not domain.endswith(f".{brand}.org"):
            impersonated_brand = brand
            warnings.append(f"Possible Brand Impersonation: Domain '{domain}' contains brand string '{brand}' but is not the official domain.")
            risk_score += 0.45
            break

    # ML Phishing Classifier Fusion
    try:
        from src.risk_engine import risk_engine
        ml_res = risk_engine.predict_url({"url": raw_url})
        evidence.append(f"ML Phishing Detector: {ml_res['label']} (Probability: {ml_res['fraud_probability']:.2f}, Risk Score: {ml_res['risk_score']}/100)")
        for exp in ml_res.get("explanations", []):
            warnings.append(f"ML Factor: {exp}")
        if ml_res["label"] == "PHISHING":
            risk_score = max(risk_score, ml_res["fraud_probability"])
    except Exception:
        pass

    # Determine Risk Level
    risk_score = min(1.0, risk_score)
    if risk_score >= 0.70:
        risk_level = "HIGH"
        recommendation = "CRITICAL: Do NOT proceed with payment or enter credentials on this URL."
    elif risk_score >= 0.35:
        risk_level = "SUSPICIOUS"
        recommendation = "WARNING: Verify payee domain authenticity via official channels before proceeding."
    else:
        risk_level = "LOW"
        recommendation = "Low-risk indicators detected. Always confirm recipient identity."

    return URLScanResponse(
        url=raw_url,
        domain=domain,
        scheme=parsed.scheme,
        risk_level=risk_level,
        risk_score=round(risk_score, 2),
        evidence=evidence,
        warnings=warnings,
        recommendation=recommendation,
        is_https=is_https,
        has_ip_host=has_ip_host,
        possible_brand_impersonation=impersonated_brand,
        scanned_at=datetime.now(timezone.utc).isoformat()
    )


# ------------------------------------------------------------------------------
# 2. QR / UPI SECURITY SCANNER
# ------------------------------------------------------------------------------
class QRScanRequest(BaseModel):
    payload: str = Field(min_length=1, max_length=4_096)  # e.g., "upi://pay?pa=merchant@upi&pn=Store&am=500.00"

class QRScanResponse(BaseModel):
    qr_type: str  # UPI, URL, TEXT
    payee_id: Optional[str] = None
    payee_name: Optional[str] = None
    amount: Optional[float] = None
    risk_level: str
    risk_score: float
    evidence: List[str]
    warnings: List[str]
    recommendation: str

@router.post("/scans/qr", response_model=QRScanResponse)
def scan_qr(request: QRScanRequest):
    payload = request.payload.strip()
    evidence = []
    warnings = []
    risk_score = 0.1

    if payload.startswith("upi://pay"):
        qr_type = "UPI"
        parsed = urllib.parse.urlparse(payload)
        query = urllib.parse.parse_qs(parsed.query)
        payee_id = query.get("pa", [""])[0]
        payee_name = query.get("pn", [""])[0]
        amount_str = query.get("am", [None])[0]
        try:
            amount = float(amount_str) if amount_str else None
        except ValueError:
            raise HTTPException(status_code=422, detail="UPI amount must be numeric")

        evidence.append(f"Decoded valid UPI payment vector. Target VPA: {payee_id or 'Unspecified'}")
        if payee_name:
            evidence.append(f"Claimed Merchant / Payee Name: {payee_name}")
        
        # Risk heuristics
        if not payee_id:
            warnings.append("Missing UPI VPA ID in payment payload.")
            risk_score += 0.4
        elif any(sus in payee_id.lower() for sus in ["lottery", "winner", "reward", "support", "refund"]):
            warnings.append(f"Suspicious keyword in VPA ID: '{payee_id}'")
            risk_score += 0.35
            
        if amount and amount > 5000:
            warnings.append(f"High-value request amount: ${amount:.2f}")
            risk_score += 0.15

        # Augment with Real UPI ML Model
        try:
            from src.risk_engine import risk_engine
            upi_ml = risk_engine.predict("upi", {
                "amount (INR)": amount or 0.0,
                "transaction type": "P2M" if payee_name else "P2P"
            })
            evidence.append(f"UPI ML Model Assessment: {upi_ml['label']} (ML Probability: {upi_ml['fraud_probability']:.2f}, Risk Score: {upi_ml['risk_score']}/100)")
            for exp in upi_ml.get("explanations", []):
                evidence.append(f"ML Factor: {exp}")
        except Exception:
            pass

        risk_score = min(1.0, risk_score)
        risk_level = "HIGH" if risk_score >= 0.6 else "SUSPICIOUS" if risk_score >= 0.3 else "LOW"
        recommendation = "Verify recipient name in your banking app before confirming PIN entry."
        return QRScanResponse(
            qr_type=qr_type, payee_id=payee_id, payee_name=payee_name, amount=amount,
            risk_level=risk_level, risk_score=round(risk_score, 2),
            evidence=evidence, warnings=warnings, recommendation=recommendation
        )
    elif payload.startswith(("http://", "https://")):
        # Redirect to URL scanner logic
        url_res = scan_url(URLScanRequest(url=payload))
        return QRScanResponse(
            qr_type="URL", payee_id=None, payee_name=url_res.domain, amount=None,
            risk_level=url_res.risk_level, risk_score=url_res.risk_score,
            evidence=url_res.evidence, warnings=url_res.warnings, recommendation=url_res.recommendation
        )
    else:
        return QRScanResponse(
            qr_type="TEXT", payee_id=None, payee_name=None, amount=None,
            risk_level="LOW", risk_score=0.05,
            evidence=["Generic text QR payload decoded successfully."], warnings=[],
            recommendation="Plain text QR payload. No automatic execution triggered."
        )


class UPIPredictionRequest(BaseModel):
    amount: float = Field(..., ge=0)
    transaction_type: str = Field(default="P2P")
    merchant_category: str = Field(default="Shopping")
    sender_age_group: str = Field(default="26-35")
    receiver_age_group: str = Field(default="26-35")
    sender_state: str = Field(default="Delhi")
    sender_bank: str = Field(default="HDFC")
    receiver_bank: str = Field(default="SBI")
    device_type: str = Field(default="Android")
    network_type: str = Field(default="4G")
    hour_of_day: int = Field(default=12, ge=0, le=23)
    day_of_week: str = Field(default="Monday")

@router.post("/predict/upi")
def predict_upi_transaction(request: UPIPredictionRequest):
    from src.risk_engine import risk_engine
    return risk_engine.predict("upi", request.model_dump())


# ------------------------------------------------------------------------------
# 3. SMS & EMAIL SCAM ANALYZERS
# ------------------------------------------------------------------------------
class TextAnalysisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)

class TextAnalysisResponse(BaseModel):
    scam_category: str  # PHISHING, FAKE_KYC, REFUND_SCAM, OTP_HARVESTING, INVESTMENT_SCAM, SAFE
    risk_level: str
    risk_score: float
    detected_phrases: List[str]
    urgency_detected: bool
    financial_request: bool
    recommendation: str

@router.post("/scans/sms", response_model=TextAnalysisResponse)
@router.post("/scans/email", response_model=TextAnalysisResponse)
def analyze_scam_text(request: TextAnalysisRequest):
    text = request.text.strip().lower()
    phrases = []
    risk_score = 0.05
    category = "SAFE"
    urgency = False
    financial = False

    # Keywords & Patterns
    if any(k in text for k in ["kyc", "account blocked", "suspend", "update immediately"]):
        category = "FAKE_KYC"
        phrases.append("Account suspension / KYC threat")
        risk_score += 0.45
        urgency = True

    if any(k in text for k in ["otp", "code", "pin", "verify your login"]):
        category = "OTP_HARVESTING" if category == "SAFE" else category
        phrases.append("Credential or OTP verification request")
        risk_score += 0.50

    if any(k in text for k in ["refund", "cashback", "reward", "lottery", "won"]):
        category = "REFUND_SCAM" if category == "SAFE" else category
        phrases.append("Unsolicited financial reward or refund promise")
        risk_score += 0.40
        financial = True

    if any(k in text for k in ["urgent", "within 24 hours", "action required"]):
        urgency = True
        phrases.append("Artificial pressure / urgency tactic")
        risk_score += 0.20

    if re.search(r'https?://[^\s]+', text):
        phrases.append("Embedded link detected in message")
        risk_score += 0.25

    # ML NLP Scam Classifier Fusion
    try:
        from src.risk_engine import risk_engine
        sms_ml = risk_engine.predict_sms({"text": request.text})
        if sms_ml["label"] == "SPAM_SCAM":
            risk_score = max(risk_score, sms_ml["fraud_probability"])
            phrases.append(f"ML Classifier: Scam pattern detected ({sms_ml['fraud_probability']:.2f} confidence)")
            for exp in sms_ml.get("explanations", []):
                phrases.append(f"ML Pattern: {exp}")
            if category == "SAFE":
                category = "PHISHING"
    except Exception:
        pass

    risk_score = min(1.0, risk_score)
    risk_level = "CRITICAL" if risk_score >= 0.8 else "HIGH" if risk_score >= 0.6 else "SUSPICIOUS" if risk_score >= 0.3 else "LOW"
    recommendation = "Do NOT click links, disclose OTPs, or call listed numbers. Verify via official banking portals only."

    return TextAnalysisResponse(
        scam_category=category,
        risk_level=risk_level,
        risk_score=round(risk_score, 2),
        detected_phrases=phrases,
        urgency_detected=urgency,
        financial_request=financial,
        recommendation=recommendation
    )


# ------------------------------------------------------------------------------
# 4. FRAUDSENSE AI COPILOT & INVESTIGATION AGENT
# ------------------------------------------------------------------------------
class CopilotRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)
    context: Optional[dict] = None

class CopilotResponse(BaseModel):
    reply: str
    risk_assessment: Optional[dict] = None
    recommended_tools: List[str] = []

@router.post("/copilot/chat", response_model=CopilotResponse)
def copilot_chat(request: CopilotRequest):
    query = request.message.strip().lower()
    
    # Tool invocation heuristics
    if "http" in query or "link" in query or "url" in query:
        # Extract link
        links = re.findall(r'https?://[^\s]+', query)
        if links:
            scan_res = scan_url(URLScanRequest(url=links[0]))
            return CopilotResponse(
                reply=f"I performed a real-time security scan on `{links[0]}`. **Risk Level: {scan_res.risk_level}** ({scan_res.risk_score * 100:.0f}% risk).\n\n**Evidence:**\n" + "\n".join([f"- {w}" for w in scan_res.warnings or ["No critical warnings"]]) + f"\n\n**Recommendation:** {scan_res.recommendation}",
                risk_assessment=scan_res.model_dump(),
                recommended_tools=["analyze_url", "domain_intelligence"]
            )

    if any(k in query for k in ["sms", "text", "message", "kyc", "otp"]):
        scan_res = analyze_scam_text(TextAnalysisRequest(text=query))
        return CopilotResponse(
            reply=f"Analysis completed on your message. Detected Pattern: **{scan_res.scam_category}** (Risk Level: **{scan_res.risk_level}**).\n\n**Signals Identified:**\n" + "\n".join([f"- {p}" for p in scan_res.detected_phrases]) + f"\n\n**Recommendation:** {scan_res.recommendation}",
            risk_assessment=scan_res.model_dump(),
            recommended_tools=["analyze_sms", "analyze_phishing"]
        )

    # General FraudSense AI Assistance
    reply = (
        "Hello! I am your **FraudSense AI Intelligence Copilot**.\n\n"
        "I monitor financial transactions, payment URLs, UPI QR payloads, and phishing vectors in real time. "
        "You can paste a suspicious payment link, transaction ID, bank message, or ask how to investigate a fraud alert."
    )
    return CopilotResponse(reply=reply, recommended_tools=["analyze_transaction", "analyze_url", "analyze_qr"])


# ------------------------------------------------------------------------------
# 5. GLOBAL THREAT INTELLIGENCE FEED & AUDIT LOGS
# ------------------------------------------------------------------------------
@router.get("/threat-intelligence")
def get_threat_intelligence():
    return [
        {
            "id": "THREAT-9041",
            "category": "Phishing Domain Wave",
            "threat_actor": "Unknown / Automated Botnet",
            "target_ecosystem": "Net Banking & UPI",
            "severity": "CRITICAL",
            "indicators": ["bank-security-verify.xyz", "update-kyc-now.top"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "THREAT-9042",
            "category": "Credential Harvesting",
            "threat_actor": "SMS-Phish Syndicate",
            "target_ecosystem": "Card-Not-Present E-commerce",
            "severity": "HIGH",
            "indicators": ["claim-reward-points.online"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "THREAT-9043",
            "category": "Fake Refund Bot",
            "threat_actor": "Telegram Scam Agent",
            "target_ecosystem": "P2P Payment Apps",
            "severity": "MEDIUM",
            "indicators": ["support-refund-desk.info"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]

@router.get("/audit/logs")
def get_audit_logs(db: Session = Depends(get_db)):
    logs = db.query(TransactionAuditLog).order_by(TransactionAuditLog.timestamp.desc()).limit(50).all()
    return logs
