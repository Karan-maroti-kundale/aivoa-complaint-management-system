from datetime import date
from pydantic import BaseModel, Field, ConfigDict

class ComplaintData(BaseModel):
    complaint_source: str | None = None
    facility: str | None = None
    material_impact: str | None = None
    customer_name: str | None = None
    product_name: str | None = None
    product_strength: str | None = None
    batch_number: str | None = None
    affected_quantity: str | None = None
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    complaint_type: str | None = None
    complaint_date: date | None = None
    description: str | None = None
    severity: str | None = None
    priority: str | None = None
    risk_assessment: str | None = None
    suggested_next_action: str | None = None
    completeness_score: int = Field(default=0, ge=0, le=100)
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)

class ComplaintResponse(ComplaintData):
    model_config = ConfigDict(from_attributes=True)
    id: int
    complaint_number: str
    source: str
    status: str
    committed: bool

class CopilotRequest(BaseModel):
    complaint_id: int | None = None
    message: str

class CopilotResponse(BaseModel):
    complaint_id: int
    reply: str
    complaint: ComplaintResponse
    ai_tools: dict

class CommitResponse(BaseModel):
    complaint: ComplaintResponse
    ledger_id: str
    message: str
