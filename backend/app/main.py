from datetime import date, datetime
from uuid import uuid4

from fastapi import FastAPI, Depends, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import CORS_ORIGINS
from app.db.database import Base, engine, get_db
from app.models.complaint import Complaint, AuditEvent
from app.schemas.complaint import (
    ComplaintResponse,
    CopilotRequest,
    CopilotResponse,
    CommitResponse,
)
from app.agents.graph import graph
from app.services.text_extract import extract_document_text


# -------------------------------------------------------------------
# FastAPI application
# -------------------------------------------------------------------

app = FastAPI(
    title="AIVOA Complaint AI",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Startup
# -------------------------------------------------------------------

@app.on_event("startup")
def startup():
    """
    Create database tables and apply safe additive migrations.
    """
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE complaints "
                "ADD COLUMN IF NOT EXISTS facility VARCHAR(200)"
            )
        )

        conn.execute(
            text(
                "ALTER TABLE complaints "
                "ADD COLUMN IF NOT EXISTS material_impact VARCHAR(200)"
            )
        )


# -------------------------------------------------------------------
# Utility helpers
# -------------------------------------------------------------------

def parse_date_value(value):
    """
    Convert supported date representations into a Python date.

    Supported:
    - None
    - date
    - datetime
    - ISO date string: YYYY-MM-DD

    Invalid values are returned as None instead of crashing the request.
    """
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        # Expected AI/backend format
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass

        # Common human-readable formats
        formats = [
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m-%d-%Y",
            "%m/%d/%Y",
            "%B %Y",
            "%b %Y",
            "%B %d, %Y",
            "%b %d, %Y",
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.date()
            except ValueError:
                continue

    return None


def missing_fields(c: Complaint):
    """
    Return all mandatory complaint fields that are currently missing.
    """
    required = [
        "complaint_source",
        "customer_name",
        "product_name",
        "product_strength",
        "batch_number",
        "affected_quantity",
        "manufacturing_date",
        "expiry_date",
        "complaint_type",
        "description",
    ]

    return [
        field
        for field in required
        if not getattr(c, field, None)
    ]


def confidence_for(c: Complaint):
    """
    Synthetic confidence score used by the demo workflow.
    """
    complaint_type = c.complaint_type or ""
    description = c.description or ""

    if (
        complaint_type == "Foreign Matter Contamination"
        or "particle" in description.lower()
    ):
        return 0.94

    if "Discoloration" in complaint_type:
        return 0.91

    return 0.78


def complaint_dict(c: Complaint):
    """
    Convert SQLAlchemy Complaint into a frontend/API friendly dictionary.

    Dates are returned as ISO strings so the response remains JSON-safe.
    """
    def date_to_string(value):
        if value is None:
            return None

        if isinstance(value, (date, datetime)):
            return value.isoformat()

        return str(value)

    return {
        "complaint_source": c.complaint_source,
        "customer_name": c.customer_name,
        "facility": c.facility,
        "material_impact": c.material_impact,
        "product_name": c.product_name,
        "product_strength": c.product_strength,
        "batch_number": c.batch_number,
        "affected_quantity": c.affected_quantity,
        "manufacturing_date": date_to_string(c.manufacturing_date),
        "expiry_date": date_to_string(c.expiry_date),
        "complaint_type": c.complaint_type,
        "complaint_date": date_to_string(c.complaint_date),
        "description": c.description,
        "severity": c.severity,
        "priority": c.priority,
        "risk_assessment": c.risk_assessment,
        "suggested_next_action": c.suggested_next_action,
        "completeness_score": c.completeness_score or 0,
        "missing_fields": missing_fields(c),
        "confidence": confidence_for(c),
        "id": c.id,
        "complaint_number": c.complaint_number,
        "source": c.source,
        "status": c.status,
        "committed": bool(c.committed),
    }


def refresh_completeness_and_status(c: Complaint):
    """
    Recalculate complaint readiness after extraction/correction.

    >= 80%  -> Ready to Commit
    < 80%   -> Review Required

    A committed complaint remains Committed to QMS.
    """
    missing = missing_fields(c)

    total_required = 10
    completed = total_required - len(missing)

    c.completeness_score = int(
        round((completed / total_required) * 100)
    )

    if c.committed:
        c.status = "Committed to QMS"
    elif c.completeness_score >= 80:
        c.status = "Ready to Commit"
    else:
        c.status = "Review Required"


def apply_data(c: Complaint, data: dict):
    """
    Safely apply structured AI output to a complaint.

    Existing non-empty values are not destroyed by None/empty AI values.
    This is especially important for conversational corrections.
    """

    text_fields = [
        "complaint_source",
        "customer_name",
        "facility",
        "material_impact",
        "product_name",
        "product_strength",
        "batch_number",
        "affected_quantity",
        "complaint_type",
        "description",
        "severity",
        "priority",
        "risk_assessment",
        "suggested_next_action",
    ]

    for field in text_fields:
        if field not in data:
            continue

        value = data.get(field)

        if value is not None and str(value).strip() != "":
            setattr(c, field, value)

    date_fields = [
        "manufacturing_date",
        "expiry_date",
        "complaint_date",
    ]

    for field in date_fields:
        if field not in data:
            continue

        value = data.get(field)

        if value in (None, ""):
            continue

        parsed = parse_date_value(value)

        if parsed is not None:
            setattr(c, field, parsed)

    # Only replace completeness when the AI explicitly returned it.
    if "completeness_score" in data and data.get("completeness_score") is not None:
        try:
            c.completeness_score = int(data["completeness_score"])
        except (TypeError, ValueError):
            pass

    refresh_completeness_and_status(c)


def log_event(
    db: Session,
    complaint_number: str,
    event_type: str,
    message: str,
    actor: str = "system",
):
    """
    Add one audit event.
    """
    event = AuditEvent(
        complaint_number=complaint_number,
        event_type=event_type,
        message=message,
        actor_type=actor,
    )

    db.add(event)
    db.commit()


def tool_payload(c: Complaint):
    """
    Synthetic demo AI tools:
    - Risk
    - Completeness
    - Duplicate detection
    - Root cause
    - CAPA
    """

    high_risk = c.severity in {"Critical", "Major"}

    duplicate_candidates = []

    if c.batch_number:
        duplicate_candidates = [
            {
                "complaint_number": "CC-2026-00091",
                "similarity": 0.89,
                "reason": "Same product/batch pattern in synthetic demo data",
            }
        ]

    return {
        "risk": {
            "severity": c.severity or "Medium",
            "priority": c.priority or "High",
            "confidence": 0.91,
            "assessment": c.risk_assessment or "Pending",
        },
        "completeness": {
            "score": c.completeness_score or 0,
            "status": (
                "Complete"
                if (c.completeness_score or 0) >= 90
                else "Needs Review"
            ),
            "missing_fields": missing_fields(c),
        },
        "duplicates": duplicate_candidates,
        "root_cause": (
            [
                "Packaging integrity deviation",
                "Material contamination during handling",
            ]
            if high_risk
            else [
                "Process or storage deviation",
            ]
        ),
        "capa": [
            "Quarantine and investigate affected batch",
            "Review manufacturing and packaging records",
            "Document corrective and preventive actions",
        ],
    }


# -------------------------------------------------------------------
# Health
# -------------------------------------------------------------------

@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "service": "aivoa-backend",
    }


# -------------------------------------------------------------------
# Text complaint intake
# -------------------------------------------------------------------

@app.post(
    "/api/v1/complaints/text",
    response_model=CopilotResponse,
)
def complaint_from_text(
    req: CopilotRequest,
    db: Session = Depends(get_db),
):
    result = graph.invoke(
        {
            "text": req.message,
            "mode": "extract",
        }
    )

    c = Complaint(
        complaint_number=(
            f"CC-{datetime.now().strftime('%Y%m%d')}-"
            f"{uuid4().hex[:6].upper()}"
        ),
        source="Copilot",
        raw_input=req.message,
    )

    apply_data(
        c,
        result.get("complaint", {}),
    )

    db.add(c)
    db.commit()
    db.refresh(c)

    # ---------------------------------------------------------------
    # Audit: extraction
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "AI_EXTRACTION",
        "Complaint extracted from Copilot text input.",
    )

    # ---------------------------------------------------------------
    # Audit: risk
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "RISK_ASSESSMENT",
        (
            "AI risk assessment generated: "
            f"{c.severity or 'Unknown'} severity."
        ),
    )

    # ---------------------------------------------------------------
    # Audit: completeness
    # ---------------------------------------------------------------

    if c.completeness_score >= 90:
        log_event(
            db,
            c.complaint_number,
            "COMPLETENESS_CHECK",
            (
                "Complaint completeness check passed at "
                f"{c.completeness_score}%."
            ),
        )
    else:
        log_event(
            db,
            c.complaint_number,
            "COMPLETENESS_CHECK",
            (
                "Complaint completeness is "
                f"{c.completeness_score}%; "
                "review missing fields."
            ),
        )

    # ---------------------------------------------------------------
    # Final response
    # ---------------------------------------------------------------

    return {
        "complaint_id": c.id,
        "reply": result.get(
            "reply",
            "Complaint parsed successfully.",
        ),
        "complaint": complaint_dict(c),
        "ai_tools": tool_payload(c),
    }


# -------------------------------------------------------------------
# PDF / DOCX / TXT / EML complaint upload
# -------------------------------------------------------------------

@app.post(
    "/api/v1/complaints/upload",
    response_model=CopilotResponse,
)
async def complaint_from_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    filename = file.filename or "upload"

    data = await file.read()

    try:
        extracted_text = extract_document_text(
            filename,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Document parsing failed: {exc}",
        ) from exc

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No extractable text found in the uploaded document.",
        )

    result = graph.invoke(
        {
            "text": extracted_text,
            "mode": "extract",
        }
    )

    c = Complaint(
        complaint_number=(
            f"CC-{datetime.now().strftime('%Y%m%d')}-"
            f"{uuid4().hex[:6].upper()}"
        ),
        source="PDF Upload",
        raw_input=extracted_text,
    )

    apply_data(
        c,
        result.get("complaint", {}),
    )

    db.add(c)
    db.commit()
    db.refresh(c)

    # ---------------------------------------------------------------
    # Audit: document upload
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "DOCUMENT_UPLOAD",
        f"Uploaded complaint document: {filename}",
        actor="user",
    )

    # ---------------------------------------------------------------
    # Audit: document analysis
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "DOCUMENT_ANALYZED",
        f"Analyzed uploaded document: {filename}",
    )

    # ---------------------------------------------------------------
    # Audit: extraction
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "AI_EXTRACTION",
        "Complaint fields extracted from uploaded document.",
    )

    # ---------------------------------------------------------------
    # Audit: risk
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "RISK_ASSESSMENT",
        (
            "AI risk assessment generated: "
            f"{c.severity or 'Unknown'} severity."
        ),
    )

    # ---------------------------------------------------------------
    # Audit: completeness
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "COMPLETENESS_CHECK",
        (
            f"Complaint completeness evaluated at "
            f"{c.completeness_score}%."
        ),
    )

    return {
        "complaint_id": c.id,
        "reply": result.get(
            "reply",
            "Complaint parsed successfully.",
        ),
        "complaint": complaint_dict(c),
        "ai_tools": tool_payload(c),
    }


# -------------------------------------------------------------------
# Copilot correction
# -------------------------------------------------------------------

@app.post(
    "/api/v1/copilot/message",
    response_model=CopilotResponse,
)
def copilot(
    req: CopilotRequest,
    db: Session = Depends(get_db),
):
    if not req.complaint_id:
        raise HTTPException(
            status_code=400,
            detail="complaint_id is required for corrections.",
        )

    c = db.get(
        Complaint,
        req.complaint_id,
    )

    if not c:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    existing = complaint_dict(c)

    # graph.py in V4 handles JSON-safe serialization of the existing
    # complaint state, including date values.
    result = graph.invoke(
        {
            "text": req.message,
            "mode": "correction",
            "existing": existing,
        }
    )

    # ---------------------------------------------------------------
    # Apply corrected fields
    # ---------------------------------------------------------------

    apply_data(
        c,
        result.get("complaint", {}),
    )

    db.commit()
    db.refresh(c)

    # ---------------------------------------------------------------
    # Audit: user correction
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "USER_CORRECTION",
        req.message,
        actor="user",
    )

    # ---------------------------------------------------------------
    # Audit: AI correction
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "AI_CORRECTION",
        result.get(
            "reply",
            "Complaint fields updated from user correction.",
        ),
    )

    # ---------------------------------------------------------------
    # Re-check completeness
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "COMPLETENESS_CHECK",
        (
            f"Complaint completeness rechecked at "
            f"{c.completeness_score}% after correction."
        ),
    )

    return {
        "complaint_id": c.id,
        "reply": result.get(
            "reply",
            "Complaint information updated successfully.",
        ),
        "complaint": complaint_dict(c),
        "ai_tools": tool_payload(c),
    }


# -------------------------------------------------------------------
# Get complaint
# -------------------------------------------------------------------

@app.get(
    "/api/v1/complaints/{complaint_id}",
    response_model=ComplaintResponse,
)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
):
    c = db.get(
        Complaint,
        complaint_id,
    )

    if not c:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    return complaint_dict(c)


# -------------------------------------------------------------------
# QMS commit
# -------------------------------------------------------------------

@app.post(
    "/api/v1/complaints/{complaint_id}/commit",
    response_model=CommitResponse,
)
def commit(
    complaint_id: int,
    db: Session = Depends(get_db),
):
    c = db.get(
        Complaint,
        complaint_id,
    )

    if not c:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    if c.committed:
        raise HTTPException(
            status_code=400,
            detail="Complaint is already committed to the QMS.",
        )

    # The final workflow requires the complaint to be sufficiently
    # complete before commitment.
    if c.completeness_score < 80:
        raise HTTPException(
            status_code=400,
            detail=(
                "Complaint is too incomplete to commit. "
                "Complete required fields first."
            ),
        )

    # ---------------------------------------------------------------
    # Review approval
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "REVIEW_APPROVED",
        "Complaint reviewed and approved for QMS commitment.",
        actor="user",
    )

    # ---------------------------------------------------------------
    # Generate synthetic QMS ledger ID
    # ---------------------------------------------------------------

    ledger_id = (
        f"QMS-{datetime.now().strftime('%Y%m%d%H%M%S')}-"
        f"{uuid4().hex[:4].upper()}"
    )

    # ---------------------------------------------------------------
    # Commit
    # ---------------------------------------------------------------

    c.committed = True
    c.status = "Committed to QMS"

    db.commit()
    db.refresh(c)

    # ---------------------------------------------------------------
    # Audit
    # ---------------------------------------------------------------

    log_event(
        db,
        c.complaint_number,
        "QMS_COMMIT",
        (
            "Committed to synthetic QMS ledger as "
            f"{ledger_id}"
        ),
        actor="user",
    )

    return {
        "complaint": complaint_dict(c),
        "ledger_id": ledger_id,
        "message": (
            "Complaint successfully committed "
            "to the QMS ledger."
        ),
    }


# -------------------------------------------------------------------
# Audit timeline
# -------------------------------------------------------------------

@app.get(
    "/api/v1/complaints/{complaint_id}/audit"
)
def audit(
    complaint_id: int,
    db: Session = Depends(get_db),
):
    c = db.get(
        Complaint,
        complaint_id,
    )

    if not c:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    events = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.complaint_number
            == c.complaint_number
        )
        .order_by(
            AuditEvent.created_at.asc()
        )
        .all()
    )

    return [
        {
            "event_type": event.event_type,
            "actor_type": event.actor_type,
            "message": event.message,
            "created_at": event.created_at,
        }
        for event in events
    ]