import re
from typing import Any

DEFAULT = {
    "complaint_source": None,
    "customer_name": None,
    "product_name": None,
    "product_strength": None,
    "batch_number": None,
    "affected_quantity": None,
    "manufacturing_date": None,
    "expiry_date": None,
    "complaint_type": None,
    "complaint_date": None,
    "description": None,
    "severity": "Medium",
    "priority": "High",
    "risk_assessment": "Initial AI assessment pending further review.",
    "suggested_next_action": "Review complaint details, verify batch records, and initiate QA assessment.",
    "completeness_score": 0,
    "missing_fields": [],
    "confidence": 0.65,
}

MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}


def first(pattern: str, text: str, flags=re.I) -> str | None:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def _clean(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip().strip('"')
        return value or None
    return value


def _date_from_month_year(month: str, year: str, day: str = "01") -> str:
    return f"{year}-{MONTHS[month.lower()]}-{day}"


def _parse_dates(text: str, d: dict) -> None:
    # Prefer explicit labeled dates; this prevents manufacturing/expiry inversion.
    patterns = {
        "manufacturing_date": r"manufacturing\s*date\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        "expiry_date": r"expiry\s*date\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        "complaint_date": r"complaint\s*date\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})",
    }
    for key, pat in patterns.items():
        value = first(pat, text)
        if value:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                d[key] = value
            else:
                # For demo input in DD/MM/YYYY form.
                dd, mm, yyyy = re.split(r"[/-]", value)
                d[key] = f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"

    # Natural month/year phrases such as "Manufacturing date March 2026".
    for key, label in [("manufacturing_date", "manufacturing"), ("expiry_date", "expiry"), ("complaint_date", "complaint")]:
        if d.get(key):
            continue
        m = re.search(fr"{label}\s*date\s*[:\-]?\s*(\w+)\s+(20\d{{2}})", text, re.I)
        if m and m.group(1).lower() in MONTHS:
            d[key] = _date_from_month_year(m.group(1), m.group(2))

    # Unlabeled phrases in the specific demo order: manufacturing, then expiry.
    if not d.get("manufacturing_date"):
        m = re.search(r"manufacturing\s+date\s+(\w+)\s+(20\d{2})", text, re.I)
        if m and m.group(1).lower() in MONTHS:
            d["manufacturing_date"] = _date_from_month_year(m.group(1), m.group(2))
    if not d.get("expiry_date"):
        m = re.search(r"expiry\s+date\s+(\w+)\s+(20\d{2})", text, re.I)
        if m and m.group(1).lower() in MONTHS:
            d["expiry_date"] = _date_from_month_year(m.group(1), m.group(2), "28")


def mock_extract(text: str) -> dict:
    t = text.strip()
    d = DEFAULT.copy()
    d["description"] = t

    # Explicit document/email labels.
    d["complaint_source"] = first(r"(?:complaint\s*source|source)\s*[:\-]\s*([^\n]+)", t)
    d["customer_name"] = first(r"(?:customer(?:\s*name)?)\s*[:\-]\s*([^\n]+)", t)
    d["product_name"] = first(r"product\s*[:\-]\s*([^\n]+)", t)
    d["product_strength"] = first(r"product\s*strength(?:\s*/\s*grade)?\s*[:\-]\s*([^\n]+)", t)
    d["batch_number"] = first(r"(?:batch\s*(?:/\s*lot)?\s*(?:number)?|lot\s*(?:number)?)\s*[:\-]\s*([A-Z0-9][A-Z0-9\-]+)", t)
    d["affected_quantity"] = first(r"affected\s*quantity\s*[:\-]\s*([^\n]+)", t)
    d["complaint_type"] = first(r"complaint\s*(?:type|category)\s*[:\-]\s*([^\n]+)", t)
    labeled_desc = first(r"detailed\s*complaint\s*[:\-]\s*(.+)$", t, re.I | re.S)
    if labeled_desc:
        d["description"] = labeled_desc.strip()

    # Natural-language fallbacks matching the supplied demo complaint.
    d["customer_name"] = _clean(d["customer_name"]) or first(r"(Apollo Pharmacy|ABC Formulations(?:\s+Ltd\.)?|XYZ Pharma)", t)
    d["complaint_source"] = _clean(d["complaint_source"]) or (
        "Pharmacy" if re.search(r"\bApollo Pharmacy\b", t, re.I) else ("Email" if re.search(r"\bemail\b", t, re.I) else None)
    )
    d["facility"] = first(r"(?:facility|site|plant)\s*[:\-]\s*([^\n]+)", t)
    if not d["facility"] and re.search(r"incoming quality inspection", t, re.I):
        d["facility"] = "Customer Receiving / Incoming QA"
    d["material_impact"] = first(r"(?:material|stock)\s*(?:impact|status)\s*[:\-]\s*([^\n]+)", t)
    if not d["material_impact"] and re.search(r"quarantined|quarantine", t, re.I):
        d["material_impact"] = "Quarantined"
    d["product_name"] = _clean(d["product_name"]) or first(r"(Amoxicillin Capsules|Metformin Hydrochloride API)", t)
    d["product_strength"] = _clean(d["product_strength"]) or first(r"((?:500|200)\s*mg)", t) or first(r"\b(IP/BP(?:\s+Grade)?)\b", t)
    d["batch_number"] = _clean(d["batch_number"]) or first(r"(?:batch\s*(?:number|no\.?))\s*(?:is|=|:)?\s*([A-Z0-9][A-Z0-9\-]+)", t)
    d["affected_quantity"] = _clean(d["affected_quantity"])
    if not d["affected_quantity"]:
        d["affected_quantity"] = first(r"(?:reported|contains?|found)\s+(\d+\s+(?:(?:discolored|affected|dark|foreign)\s+)?(?:capsules?|tablets?|kg|g|units?))", t)
    if not d["affected_quantity"]:
        d["affected_quantity"] = first(r"affected\s+(?:quantity|amount)\s*(?:is|=|:)\s*([^,.\n]+)", t)

    _parse_dates(t, d)

    low = t.lower()
    if not d["complaint_type"]:
        if any(x in low for x in ["foreign matter", "contamination", "particles"]):
            d["complaint_type"] = "Foreign Matter Contamination"
        elif any(x in low for x in ["discolor", "color", "colour"]):
            d["complaint_type"] = "Product Defect - Discoloration"
        else:
            d["complaint_type"] = "Other"

    if any(x in low for x in ["foreign matter", "contamination", "particles"]):
        d["severity"] = "Critical"
        d["priority"] = "Urgent"
        d["risk_assessment"] = "Potential foreign matter contamination. High impact to API quality. Investigation of manufacturing, handling and laboratory results is required."
        d["suggested_next_action"] = "Laboratory investigation and manufacturing record review; quarantine affected material and preserve samples."
        d["confidence"] = 0.94
    elif any(x in low for x in ["discolor", "color", "colour"]):
        d["severity"] = "Major"
        d["priority"] = "High"
        d["risk_assessment"] = "Potential product quality deviation. Verify retain samples, batch records and analytical results before disposition."
        d["suggested_next_action"] = "Route to QA Investigation and quarantine affected stock while verifying retain samples and batch records."
        d["confidence"] = 0.91
    else:
        d["confidence"] = 0.78

    required = [
        "complaint_source", "customer_name", "product_name", "product_strength",
        "batch_number", "affected_quantity", "manufacturing_date", "expiry_date",
        "complaint_type", "description",
    ]
    missing = [f for f in required if not d.get(f)]
    d["missing_fields"] = missing
    d["completeness_score"] = round((len(required) - len(missing)) / len(required) * 100)
    return d


def apply_correction(existing: dict, message: str) -> dict:
    out = dict(existing)
    low = message.lower()

    m = re.search(r"batch(?:\s*/\s*lot)?(?:\s*(?:number|no\.?)?)?\s*(?:is|=|:)\s*([A-Z0-9\-]+)", message, re.I)
    if m:
        out["batch_number"] = m.group(1).upper()

    m = re.search(r"affected\s*quantity\s*(?:is|=|:)\s*([^,.;\n]+)", message, re.I)
    if m:
        out["affected_quantity"] = m.group(1).strip()

    m = re.search(r"customer(?:\s*name)?\s*(?:is|=|:)\s*([^,.;\n]+)", message, re.I)
    if m:
        out["customer_name"] = m.group(1).strip()

    m = re.search(r"product(?:\s*name)?\s*(?:is|=|:)\s*([^,.;\n]+)", message, re.I)
    if m:
        out["product_name"] = m.group(1).strip()

    m = re.search(r"complaint\s*(?:source)\s*(?:is|=|:)\s*([^,.;\n]+)", message, re.I)
    if m:
        out["complaint_source"] = m.group(1).strip()

    if "severity" in low:
        for severity in ["critical", "major", "medium", "low"]:
            if severity in low:
                out["severity"] = severity.title()
                break

    required = [
        "complaint_source", "customer_name", "product_name", "product_strength",
        "batch_number", "affected_quantity", "manufacturing_date", "expiry_date",
        "complaint_type", "description",
    ]
    missing = [f for f in required if not out.get(f)]
    out["missing_fields"] = missing
    out["completeness_score"] = round((len(required) - len(missing)) / len(required) * 100)
    return out
