"""
FraudSense AI Copilot — Upload & File Analysis Routes.

POST /api/v1/copilot/upload     — Multipart file upload + analysis
GET  /api/v1/copilot/analysis/{id} — Retrieve previous analysis result
DELETE /api/v1/copilot/files/{id}  — Delete uploaded file + result
"""
from __future__ import annotations

import csv
import email
import hashlib
import io
import json
import logging
import os
import re
import secrets
import tempfile
import time
import uuid
from datetime import datetime, timezone
from email import policy as email_policy
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["copilot-uploads"])

# ── Configuration ────────────────────────────────────────────────────────────

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_CSV_ROWS = 10_000
MAX_PDF_PAGES = 200
UPLOAD_DIR = Path(tempfile.gettempdir()) / "fraudsense_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS: dict[str, list[str]] = {
    "image": [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif"],
    "document": [".pdf", ".txt", ".docx"],
    "data": [".csv", ".xlsx", ".json"],
    "evidence": [".eml"],
}
ALL_ALLOWED = {ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts}

MIME_SIGNATURES: dict[bytes, str] = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "image/webp",     # RIFF....WEBP
    b"II\x2a\x00": "image/tiff",
    b"MM\x00\x2a": "image/tiff",
    b"%PDF": "application/pdf",
    b"PK\x03\x04": "application/zip",  # xlsx/docx
}

BLOCKED_PATTERNS = [
    re.compile(r"\.{2,}"),      # Path traversal
    re.compile(r"[\x00-\x1f]"), # Control chars
    re.compile(r"[/\\]"),       # Slashes
]

# ── In-memory result store (sufficient for single-node; replace with DB for prod) ──

_analysis_store: dict[str, dict] = {}

# ── Schemas ──────────────────────────────────────────────────────────────────

class UploadAnalysisResult(BaseModel):
    analysis_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    category: str
    status: str  # completed, failed, partial
    summary: str
    extracted_text: Optional[str] = None
    extracted_urls: list[str] = Field(default_factory=list)
    extracted_transactions: Optional[list[dict]] = None
    scanner_results: Optional[list[dict]] = None
    model_predictions: Optional[list[dict]] = None
    risk_level: str = "UNKNOWN"
    risk_indicators: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    analyzed_at: str = ""

# ── Helpers ──────────────────────────────────────────────────────────────────

def _safe_filename(name: str) -> str:
    """Sanitize filename, keep only the extension for identification."""
    for pat in BLOCKED_PATTERNS:
        name = pat.sub("", name)
    return name.strip().replace(" ", "_")[:128] or "upload"


def _detect_mime(header_bytes: bytes) -> str | None:
    """Check magic bytes against known file signatures."""
    for sig, mime in MIME_SIGNATURES.items():
        if header_bytes[:len(sig)] == sig:
            return mime
    return None


def _extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    return list(set(re.findall(r'https?://[^\s<>"\')\]]+', text)))


def _compute_risk(warnings: list[str], evidence: list[str]) -> str:
    """Derive risk level from warning count and keywords."""
    critical_kw = ["malicious", "phishing", "confirmed fraud", "critical"]
    high_kw = ["suspicious", "high-risk", "scam", "impersonation"]
    txt = " ".join(warnings + evidence).lower()
    if any(k in txt for k in critical_kw):
        return "CRITICAL"
    if len(warnings) >= 5 or any(k in txt for k in high_kw):
        return "HIGH"
    if len(warnings) >= 2:
        return "SUSPICIOUS"
    if len(warnings) >= 1:
        return "LOW"
    return "NONE"


# ── File Processors ──────────────────────────────────────────────────────────

def _process_image(data: bytes, filename: str) -> dict:
    """Process image: decode QR codes, extract metadata."""
    result: dict[str, Any] = {
        "category": "QR & Payment Images",
        "extracted_text": None,
        "extracted_urls": [],
        "evidence": [],
        "warnings": [],
        "recommendations": [],
        "metadata": {},
        "scanner_results": [],
    }

    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        result["metadata"]["format"] = img.format or "unknown"
        result["metadata"]["size"] = f"{img.width}x{img.height}"
        result["metadata"]["mode"] = img.mode
        result["evidence"].append(f"Image loaded: {img.width}×{img.height} {img.format or 'image'}")
    except Exception as e:
        result["warnings"].append(f"Image load failed: {str(e)[:100]}")
        return result

    # QR Code decoding
    qr_decoded = False
    try:
        from pyzbar.pyzbar import decode as qr_decode
        from PIL import Image as PILImage
        qr_results = qr_decode(img)
        if qr_results:
            qr_decoded = True
            for qr in qr_results:
                payload = qr.data.decode("utf-8", errors="replace")
                qr_type = qr.type
                result["evidence"].append(f"QR code decoded ({qr_type}): {len(payload)} chars")
                result["extracted_text"] = (result.get("extracted_text") or "") + payload + "\n"
                result["metadata"]["qr_type"] = qr_type

                # Analyze QR payload
                if payload.startswith("upi://pay"):
                    result["category"] = "QR & Payment Images"
                    _analyze_upi_payload(payload, result)
                elif payload.startswith(("http://", "https://")):
                    result["extracted_urls"].append(payload)
                    result["category"] = "QR & Payment Images"
                    _scan_url_internal(payload, result)
                else:
                    result["evidence"].append(f"Plain text QR payload: {payload[:200]}")
    except ImportError:
        result["warnings"].append("QR decoder (pyzbar) not available. Install zbar libraries.")
    except Exception as e:
        result["warnings"].append(f"QR decode error: {str(e)[:100]}")

    if not qr_decoded:
        result["category"] = "Screenshots & Photos"
        result["evidence"].append("No QR code found in this image. For OCR text extraction, a vision provider is required.")
        result["recommendations"].append("If this is a screenshot of a suspicious message, copy-paste the text into the Copilot chat for analysis.")

    return result


def _analyze_upi_payload(payload: str, result: dict) -> None:
    """Analyze a UPI payment URI and add findings to result."""
    import urllib.parse
    parsed = urllib.parse.urlparse(payload)
    query = urllib.parse.parse_qs(parsed.query)
    payee_id = query.get("pa", [""])[0]
    payee_name = query.get("pn", [""])[0]
    amount_str = query.get("am", [None])[0]

    result["metadata"]["upi_payee_id"] = payee_id
    result["metadata"]["upi_payee_name"] = payee_name

    if payee_id:
        result["evidence"].append(f"UPI VPA: {payee_id}")
    if payee_name:
        result["evidence"].append(f"Payee Name: {payee_name}")
    if amount_str:
        try:
            amount = float(amount_str)
            result["metadata"]["upi_amount"] = amount
            result["evidence"].append(f"Requested Amount: ₹{amount:.2f}")
            if amount > 5000:
                result["warnings"].append(f"High-value payment request: ₹{amount:.2f}")
        except ValueError:
            result["warnings"].append(f"Invalid UPI amount: {amount_str}")

    # Suspicious VPA keywords
    sus_kw = ["lottery", "winner", "reward", "support", "refund", "claim", "prize"]
    if payee_id and any(k in payee_id.lower() for k in sus_kw):
        result["warnings"].append(f"Suspicious keyword in VPA ID: '{payee_id}'")

    # Invoke existing QR scanner
    try:
        from api.intelligence_routes import scan_qr, QRScanRequest
        scan_res = scan_qr(QRScanRequest(payload=payload))
        result["scanner_results"].append({
            "scanner": "QR Security Scanner",
            "risk_level": scan_res.risk_level,
            "risk_score": scan_res.risk_score,
            "evidence": scan_res.evidence,
            "warnings": scan_res.warnings,
            "recommendation": scan_res.recommendation,
        })
        result["warnings"].extend(scan_res.warnings)
    except Exception:
        pass

    result["recommendations"].append("Verify payee identity in your official banking app before entering PIN.")


def _scan_url_internal(url: str, result: dict) -> None:
    """Run existing URL scanner and add findings."""
    try:
        from api.intelligence_routes import scan_url, URLScanRequest
        scan_res = scan_url(URLScanRequest(url=url))
        result["scanner_results"].append({
            "scanner": "Universal Link Scanner",
            "url": url,
            "risk_level": scan_res.risk_level,
            "risk_score": scan_res.risk_score,
            "evidence": scan_res.evidence,
            "warnings": scan_res.warnings,
            "recommendation": scan_res.recommendation,
        })
        result["warnings"].extend(scan_res.warnings)
    except Exception as e:
        result["warnings"].append(f"URL scan failed: {str(e)[:100]}")


def _process_pdf(data: bytes, filename: str) -> dict:
    """Extract text and metadata from PDF."""
    result: dict[str, Any] = {
        "category": "PDF & Financial Documents",
        "extracted_text": None,
        "extracted_urls": [],
        "evidence": [],
        "warnings": [],
        "recommendations": [],
        "metadata": {},
        "scanner_results": [],
        "extracted_transactions": None,
    }

    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(data))
        num_pages = len(reader.pages)

        if num_pages > MAX_PDF_PAGES:
            result["warnings"].append(f"PDF has {num_pages} pages; only first {MAX_PDF_PAGES} analyzed.")
            num_pages = MAX_PDF_PAGES

        result["metadata"]["pages"] = num_pages
        info = reader.metadata
        if info:
            result["metadata"]["author"] = str(info.author or "")[:128]
            result["metadata"]["creator"] = str(info.creator or "")[:128]
            result["metadata"]["producer"] = str(info.producer or "")[:128]
            result["metadata"]["title"] = str(info.title or "")[:256]

        texts = []
        for i, page in enumerate(reader.pages[:MAX_PDF_PAGES]):
            try:
                text = page.extract_text() or ""
                texts.append(text)
            except Exception:
                texts.append(f"[Page {i+1}: extraction failed]")

        full_text = "\n\n".join(texts)
        # Limit extracted text to 50k chars
        if len(full_text) > 50_000:
            full_text = full_text[:50_000] + "\n... [truncated]"
        result["extracted_text"] = full_text
        result["evidence"].append(f"Extracted text from {num_pages} pages ({len(full_text)} chars)")

        # Extract URLs
        urls = _extract_urls(full_text)
        result["extracted_urls"] = urls[:50]
        if urls:
            result["evidence"].append(f"Found {len(urls)} URLs in document")
            # Scan first 5 URLs
            for url in urls[:5]:
                _scan_url_internal(url, result)

        # Financial document heuristics
        _analyze_financial_text(full_text, result)

        if reader.is_encrypted:
            result["warnings"].append("PDF is encrypted or password-protected. Content extraction may be incomplete.")

    except Exception as e:
        result["warnings"].append(f"PDF processing failed: {str(e)[:200]}")
        result["status"] = "failed"

    return result


def _analyze_financial_text(text: str, result: dict) -> None:
    """Look for financial patterns in extracted text."""
    lower = text.lower()

    # Statement detection
    statement_kw = ["bank statement", "account statement", "transaction history",
                    "opening balance", "closing balance", "credit", "debit"]
    hits = [k for k in statement_kw if k in lower]
    if len(hits) >= 2:
        result["evidence"].append(f"Document appears to be a bank statement (matched: {', '.join(hits[:4])})")
        result["metadata"]["document_type"] = "bank_statement"

    # Invoice detection
    invoice_kw = ["invoice", "bill to", "due date", "total amount", "tax", "payment terms"]
    inv_hits = [k for k in invoice_kw if k in lower]
    if len(inv_hits) >= 2:
        result["evidence"].append(f"Document appears to be an invoice (matched: {', '.join(inv_hits[:4])})")
        result["metadata"]["document_type"] = result["metadata"].get("document_type", "invoice")

    # Amount patterns
    amounts = re.findall(r'[\$₹€£]\s*[\d,]+\.?\d*', text)
    if amounts:
        result["evidence"].append(f"Found {len(amounts)} monetary values in document")
        result["metadata"]["amounts_found"] = len(amounts)

    # Suspicious patterns
    sus_patterns = [
        ("urgently transfer", "Urgent transfer instruction detected"),
        ("wire transfer immediately", "Immediate wire transfer request"),
        ("click here to verify", "Suspicious verification link instruction"),
        ("your account will be suspended", "Account suspension threat"),
        ("confirm your identity", "Identity confirmation request"),
    ]
    for pattern, desc in sus_patterns:
        if pattern in lower:
            result["warnings"].append(desc)


def _process_csv(data: bytes, filename: str) -> dict:
    """Parse CSV and validate structure."""
    result: dict[str, Any] = {
        "category": "CSV & Excel Transactions",
        "extracted_text": None,
        "extracted_urls": [],
        "evidence": [],
        "warnings": [],
        "recommendations": [],
        "metadata": {},
        "scanner_results": [],
        "extracted_transactions": [],
        "model_predictions": [],
    }

    try:
        text = data.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for i, row in enumerate(reader):
            if i >= MAX_CSV_ROWS:
                result["warnings"].append(f"CSV truncated at {MAX_CSV_ROWS} rows. Remaining rows not analyzed.")
                break
            rows.append(row)

        if not rows:
            result["warnings"].append("CSV file is empty or has no data rows.")
            return result

        columns = list(rows[0].keys())
        result["metadata"]["columns"] = columns
        result["metadata"]["total_rows"] = len(rows)
        result["evidence"].append(f"CSV parsed: {len(rows)} rows × {len(columns)} columns")
        result["evidence"].append(f"Columns: {', '.join(columns[:15])}")

        # Preview first 5 rows
        result["extracted_transactions"] = rows[:5]

        # Detect domain
        domain = _detect_csv_domain(columns, rows)
        result["metadata"]["detected_domain"] = domain
        result["evidence"].append(f"Detected data domain: {domain}")

        # Duplicate detection
        if len(rows) > 1:
            seen = set()
            dupes = 0
            for row in rows:
                key = tuple(sorted(row.items()))
                if key in seen:
                    dupes += 1
                seen.add(key)
            if dupes:
                result["warnings"].append(f"Found {dupes} duplicate rows in the dataset")
            result["metadata"]["duplicate_rows"] = dupes

        # Missing values
        missing_cols = {}
        for col in columns:
            missing = sum(1 for r in rows if not r.get(col, "").strip())
            if missing > 0:
                missing_cols[col] = missing
        if missing_cols:
            worst = sorted(missing_cols.items(), key=lambda x: x[1], reverse=True)[:5]
            result["warnings"].append(
                f"Missing values detected: {', '.join(f'{c}({n})' for c, n in worst)}"
            )

        # Batch prediction for compatible domains
        if domain != "unknown" and len(rows) <= 100:
            result["recommendations"].append(
                f"Data appears compatible with the {domain.upper()} fraud model. "
                "Use the Batch Analysis page to run ML predictions on this dataset."
            )

    except UnicodeDecodeError:
        result["warnings"].append("File encoding error. Ensure the CSV is UTF-8 encoded.")
    except Exception as e:
        result["warnings"].append(f"CSV processing failed: {str(e)[:200]}")

    return result


def _detect_csv_domain(columns: list[str], rows: list[dict]) -> str:
    """Identify which fraud model domain a CSV may belong to."""
    cols_lower = {c.lower() for c in columns}
    if {"step", "type", "amount", "oldbalanceorg"} <= cols_lower:
        return "paysim"
    if {"amount", "transaction_type", "merchant_category"} <= cols_lower:
        return "upi"
    if {"v1", "v2", "v3", "amount"} <= cols_lower:
        return "card"
    if {"income", "velocity_6h", "credit_risk_score"} <= cols_lower:
        return "bank"
    if {"time_step"} <= cols_lower:
        return "bitcoin"
    if {"url"} <= cols_lower:
        return "url_phishing"
    if {"text"} <= cols_lower and any("sms" in c.lower() or "message" in c.lower() for c in columns):
        return "sms"
    return "unknown"


def _process_xlsx(data: bytes, filename: str) -> dict:
    """Parse Excel file."""
    result: dict[str, Any] = {
        "category": "CSV & Excel Transactions",
        "extracted_text": None,
        "extracted_urls": [],
        "evidence": [],
        "warnings": [],
        "recommendations": [],
        "metadata": {},
        "scanner_results": [],
        "extracted_transactions": [],
        "model_predictions": [],
    }

    try:
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        sheet = wb.active
        if not sheet:
            result["warnings"].append("Excel file has no active worksheet.")
            return result

        result["metadata"]["sheet_name"] = sheet.title
        result["metadata"]["sheets"] = wb.sheetnames

        # Read header + rows
        rows_data = []
        headers = []
        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i == 0:
                headers = [str(c or f"col_{j}") for j, c in enumerate(row)]
                continue
            if i > MAX_CSV_ROWS:
                result["warnings"].append(f"Excel truncated at {MAX_CSV_ROWS} rows.")
                break
            rows_data.append(dict(zip(headers, [str(c) if c is not None else "" for c in row])))

        wb.close()

        result["metadata"]["columns"] = headers
        result["metadata"]["total_rows"] = len(rows_data)
        result["evidence"].append(f"Excel parsed: {len(rows_data)} rows × {len(headers)} columns")
        result["evidence"].append(f"Columns: {', '.join(headers[:15])}")
        result["extracted_transactions"] = rows_data[:5]

        domain = _detect_csv_domain(headers, rows_data)
        result["metadata"]["detected_domain"] = domain
        result["evidence"].append(f"Detected data domain: {domain}")

        if domain != "unknown" and len(rows_data) <= 100:
            result["recommendations"].append(
                f"Data appears compatible with the {domain.upper()} fraud model. "
                "Use the Batch Analysis page to run ML predictions."
            )

    except Exception as e:
        result["warnings"].append(f"Excel processing failed: {str(e)[:200]}")

    return result


def _process_txt(data: bytes, filename: str) -> dict:
    """Process plain text file."""
    result: dict[str, Any] = {
        "category": "SMS, Email & Phishing Evidence",
        "extracted_text": None,
        "extracted_urls": [],
        "evidence": [],
        "warnings": [],
        "recommendations": [],
        "metadata": {},
        "scanner_results": [],
    }

    try:
        text = data.decode("utf-8", errors="replace")[:100_000]
        result["extracted_text"] = text
        result["metadata"]["length"] = len(text)
        result["evidence"].append(f"Text file: {len(text)} characters")

        urls = _extract_urls(text)
        result["extracted_urls"] = urls[:50]
        if urls:
            result["evidence"].append(f"Found {len(urls)} URLs")
            for url in urls[:5]:
                _scan_url_internal(url, result)

        # Run scam analyzer
        _run_scam_analysis(text, result)

    except Exception as e:
        result["warnings"].append(f"Text processing failed: {str(e)[:200]}")

    return result


def _process_eml(data: bytes, filename: str) -> dict:
    """Parse .eml email file."""
    result: dict[str, Any] = {
        "category": "SMS, Email & Phishing Evidence",
        "extracted_text": None,
        "extracted_urls": [],
        "evidence": [],
        "warnings": [],
        "recommendations": [],
        "metadata": {},
        "scanner_results": [],
    }

    try:
        msg = email.message_from_bytes(data, policy=email_policy.default)
        result["metadata"]["from"] = str(msg.get("From", ""))[:256]
        result["metadata"]["to"] = str(msg.get("To", ""))[:256]
        result["metadata"]["subject"] = str(msg.get("Subject", ""))[:256]
        result["metadata"]["date"] = str(msg.get("Date", ""))[:128]
        result["metadata"]["reply_to"] = str(msg.get("Reply-To", ""))[:256]

        result["evidence"].append(f"From: {result['metadata']['from']}")
        result["evidence"].append(f"Subject: {result['metadata']['subject']}")
        result["evidence"].append(f"Date: {result['metadata']['date']}")

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain":
                    body += part.get_content() + "\n"
                elif ctype == "text/html":
                    html = part.get_content()
                    # Strip HTML tags for analysis
                    body += re.sub(r'<[^>]+>', ' ', html) + "\n"
        else:
            body = msg.get_content() or ""

        body = body[:100_000]
        result["extracted_text"] = body
        result["metadata"]["body_length"] = len(body)

        # Check sender domain consistency
        from_addr = result["metadata"]["from"]
        if "<" in from_addr and ">" in from_addr:
            email_addr = from_addr.split("<")[1].split(">")[0]
            domain = email_addr.split("@")[-1] if "@" in email_addr else ""
            result["metadata"]["sender_domain"] = domain
            display_name = from_addr.split("<")[0].strip().strip('"').lower()
            # Check for brand impersonation in display name
            brands = ["paypal", "chase", "hdfc", "sbi", "icici", "amazon", "google", "microsoft", "apple"]
            for brand in brands:
                if brand in display_name and brand not in domain.lower():
                    result["warnings"].append(
                        f"Possible impersonation: display name contains '{brand}' but sender domain is '{domain}'"
                    )

        # Extract URLs from body
        urls = _extract_urls(body)
        result["extracted_urls"] = urls[:50]
        if urls:
            result["evidence"].append(f"Found {len(urls)} URLs in email body")
            for url in urls[:5]:
                _scan_url_internal(url, result)

        # Run scam text analysis on subject + body
        _run_scam_analysis(f"{result['metadata']['subject']} {body}", result)

        result["recommendations"].append("Do not click links or download attachments from suspicious emails.")
        result["recommendations"].append("Verify sender identity through official channels.")

    except Exception as e:
        result["warnings"].append(f"Email parsing failed: {str(e)[:200]}")

    return result


def _process_json_file(data: bytes, filename: str) -> dict:
    """Process JSON file — likely transaction data."""
    result: dict[str, Any] = {
        "category": "CSV & Excel Transactions",
        "extracted_text": None,
        "extracted_urls": [],
        "evidence": [],
        "warnings": [],
        "recommendations": [],
        "metadata": {},
        "scanner_results": [],
        "extracted_transactions": [],
    }

    try:
        text = data.decode("utf-8", errors="replace")[:500_000]
        parsed = json.loads(text)
        result["extracted_text"] = text[:10_000]

        if isinstance(parsed, list):
            result["metadata"]["type"] = "array"
            result["metadata"]["total_items"] = len(parsed)
            result["evidence"].append(f"JSON array with {len(parsed)} items")
            result["extracted_transactions"] = parsed[:5]
            if parsed and isinstance(parsed[0], dict):
                result["metadata"]["columns"] = list(parsed[0].keys())
        elif isinstance(parsed, dict):
            result["metadata"]["type"] = "object"
            result["metadata"]["keys"] = list(parsed.keys())[:30]
            result["evidence"].append(f"JSON object with {len(parsed)} keys")
        else:
            result["evidence"].append(f"JSON primitive: {type(parsed).__name__}")

    except json.JSONDecodeError as e:
        result["warnings"].append(f"Invalid JSON: {str(e)[:200]}")
    except Exception as e:
        result["warnings"].append(f"JSON processing failed: {str(e)[:200]}")

    return result


def _process_docx(data: bytes, filename: str) -> dict:
    """Extract text from DOCX."""
    result: dict[str, Any] = {
        "category": "PDF & Financial Documents",
        "extracted_text": None,
        "extracted_urls": [],
        "evidence": [],
        "warnings": [],
        "recommendations": [],
        "metadata": {},
        "scanner_results": [],
    }

    try:
        import zipfile
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            if "word/document.xml" not in zf.namelist():
                result["warnings"].append("Not a valid DOCX file.")
                return result
            xml_content = zf.read("word/document.xml").decode("utf-8", errors="replace")
            # Simple XML text extraction (strip tags)
            text = re.sub(r'<[^>]+>', '', xml_content)
            text = re.sub(r'\s+', ' ', text).strip()[:50_000]
            result["extracted_text"] = text
            result["evidence"].append(f"DOCX text extracted: {len(text)} characters")
            result["metadata"]["type"] = "docx"

            urls = _extract_urls(text)
            result["extracted_urls"] = urls[:50]
            if urls:
                result["evidence"].append(f"Found {len(urls)} URLs in document")
                for url in urls[:5]:
                    _scan_url_internal(url, result)

            _analyze_financial_text(text, result)

    except Exception as e:
        result["warnings"].append(f"DOCX processing failed: {str(e)[:200]}")

    return result


def _run_scam_analysis(text: str, result: dict) -> None:
    """Invoke the existing SMS/Email scam analyzer."""
    try:
        from api.intelligence_routes import analyze_scam_text, TextAnalysisRequest
        scan_res = analyze_scam_text(TextAnalysisRequest(text=text[:10_000]))
        result["scanner_results"].append({
            "scanner": "SMS & Email Scam Analyzer",
            "scam_category": scan_res.scam_category,
            "risk_level": scan_res.risk_level,
            "risk_score": scan_res.risk_score,
            "detected_phrases": scan_res.detected_phrases,
            "urgency_detected": scan_res.urgency_detected,
            "financial_request": scan_res.financial_request,
            "recommendation": scan_res.recommendation,
        })
        if scan_res.risk_level in ("HIGH", "CRITICAL"):
            result["warnings"].append(f"Scam Analyzer: {scan_res.scam_category} ({scan_res.risk_level})")
    except Exception:
        pass


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/copilot/upload", response_model=UploadAnalysisResult)
async def upload_and_analyze(
    file: UploadFile = File(...),
    user_prompt: str = Form(default=""),
):
    """Upload a file to the Copilot for automated analysis."""
    start = time.perf_counter()

    # 1. Validate filename & extension
    raw_name = _safe_filename(file.filename or "unknown")
    ext = Path(raw_name).suffix.lower()
    if ext not in ALL_ALLOWED:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{ext}'. Accepted: {', '.join(sorted(ALL_ALLOWED))}"
        )

    # 2. Read file (bounded)
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(data) / 1024 / 1024:.1f} MB). Max: {MAX_UPLOAD_BYTES / 1024 / 1024:.0f} MB."
        )
    if len(data) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    # 3. Magic-byte validation
    detected_mime = _detect_mime(data[:8])
    if ext in (".png", ".jpg", ".jpeg", ".tiff", ".tif") and detected_mime and "image" not in detected_mime:
        raise HTTPException(
            status_code=422,
            detail=f"File content does not match extension '{ext}'. Detected: {detected_mime}"
        )
    if ext == ".pdf" and detected_mime and detected_mime != "application/pdf":
        raise HTTPException(
            status_code=422,
            detail=f"File content does not match PDF extension. Detected: {detected_mime}"
        )

    # 4. Generate analysis ID
    analysis_id = f"ANA-{secrets.token_hex(6).upper()}"

    # 5. Process by type
    processor_map = {
        ".png": _process_image, ".jpg": _process_image, ".jpeg": _process_image,
        ".webp": _process_image, ".tiff": _process_image, ".tif": _process_image,
        ".pdf": _process_pdf,
        ".csv": _process_csv,
        ".xlsx": _process_xlsx,
        ".txt": _process_txt,
        ".eml": _process_eml,
        ".json": _process_json_file,
        ".docx": _process_docx,
    }

    processor = processor_map.get(ext)
    if not processor:
        raise HTTPException(status_code=422, detail=f"No processor for '{ext}'")

    try:
        proc_result = processor(data, raw_name)
    except Exception as e:
        logger.exception("File processing failed for %s", raw_name)
        proc_result = {
            "category": "Other Supported Documents",
            "evidence": [],
            "warnings": [f"Processing failed: {str(e)[:200]}"],
            "recommendations": ["Try uploading a different file or contact support."],
            "metadata": {},
        }

    # 6. Compute risk
    risk_level = _compute_risk(
        proc_result.get("warnings", []),
        proc_result.get("evidence", [])
    )

    # 7. Build summary
    evidence = proc_result.get("evidence", [])
    warnings = proc_result.get("warnings", [])
    category = proc_result.get("category", "Other Supported Documents")

    if warnings:
        summary = f"Analyzed {raw_name}. {len(warnings)} warning(s) detected. Risk: {risk_level}."
    else:
        summary = f"Analyzed {raw_name}. No suspicious indicators found."

    status = proc_result.get("status", "completed")

    elapsed_ms = (time.perf_counter() - start) * 1000

    analysis = UploadAnalysisResult(
        analysis_id=analysis_id,
        filename=raw_name,
        file_type=ext,
        file_size_bytes=len(data),
        category=category,
        status=status,
        summary=summary,
        extracted_text=proc_result.get("extracted_text"),
        extracted_urls=proc_result.get("extracted_urls", []),
        extracted_transactions=proc_result.get("extracted_transactions"),
        scanner_results=proc_result.get("scanner_results"),
        model_predictions=proc_result.get("model_predictions"),
        risk_level=risk_level,
        risk_indicators=warnings[:20],
        evidence=evidence[:30],
        warnings=warnings[:20],
        recommendations=proc_result.get("recommendations", [])[:10],
        metadata={**proc_result.get("metadata", {}), "processing_ms": round(elapsed_ms, 1)},
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )

    # Store for retrieval
    _analysis_store[analysis_id] = analysis.model_dump()

    return analysis


@router.get("/copilot/analysis/{analysis_id}")
def get_analysis(analysis_id: str):
    """Retrieve a previous analysis result."""
    result = _analysis_store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")
    return result


@router.delete("/copilot/files/{analysis_id}")
def delete_analysis(analysis_id: str):
    """Delete analysis result."""
    if analysis_id not in _analysis_store:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")
    del _analysis_store[analysis_id]
    return {"status": "deleted", "analysis_id": analysis_id}
