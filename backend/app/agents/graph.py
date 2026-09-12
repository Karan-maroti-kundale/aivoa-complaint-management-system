import json, re
from typing import TypedDict
from langgraph.graph import StateGraph, END, START
from groq import Groq
from app.core import GROQ_API_KEY, AIVOA_GROQ_MODEL
from app.agents.prompts import SYSTEM_PROMPT, CORRECTION_PROMPT
from app.agents.mock_ai import mock_extract, apply_correction

class ComplaintState(TypedDict, total=False):
    text: str
    existing: dict
    mode: str
    complaint: dict
    reply: str


def _extract_json(raw: str):
    raw = raw.strip().replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", raw, re.S)
    return json.loads(match.group(0) if match else raw)


def llm_json(system: str, user: str) -> dict | None:
    if not GROQ_API_KEY:
        return None
    try:
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=AIVOA_GROQ_MODEL,
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
            temperature=0,
            max_tokens=1400,
        )
        parsed = _extract_json(resp.choices[0].message.content or "")
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _merge_extraction(text: str, llm_result: dict | None) -> dict:
    # Deterministic baseline anchors the demo fields; the LLM may enrich non-empty values.
    baseline = mock_extract(text)
    if not llm_result:
        return baseline
    merged = dict(baseline)
    for key, value in llm_result.items():
        if value not in (None, "", [], {}):
            merged[key] = value
    # Keep the deterministic date extraction when the model returns a malformed
    # or reversed pair. The demo deliberately uses month/year phrases.
    for date_key in ("manufacturing_date", "expiry_date", "complaint_date"):
        if not isinstance(merged.get(date_key), str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", merged.get(date_key, "")):
            merged[date_key] = baseline.get(date_key)
    mfg, exp = baseline.get("manufacturing_date"), baseline.get("expiry_date")
    lmfg, lexp = merged.get("manufacturing_date"), merged.get("expiry_date")
    if lmfg and lexp and lmfg > lexp:
        merged["manufacturing_date"], merged["expiry_date"] = mfg, exp
    # Recompute critical fields using the baseline when the LLM omitted them.
    for key in ("complaint_source", "customer_name", "product_name", "product_strength",
                "batch_number", "affected_quantity", "manufacturing_date", "expiry_date",
                "complaint_type", "description", "severity", "priority",
                "risk_assessment", "suggested_next_action"):
        if not merged.get(key) and baseline.get(key):
            merged[key] = baseline[key]
    required = [
        "complaint_source", "customer_name", "product_name", "product_strength",
        "batch_number", "affected_quantity", "manufacturing_date", "expiry_date",
        "complaint_type", "description",
    ]
    missing = [f for f in required if not merged.get(f)]
    merged["missing_fields"] = missing
    merged["completeness_score"] = round((len(required) - len(missing)) / len(required) * 100)
    return merged


def extract_node(state: ComplaintState):
    text = state["text"]
    llm_result = llm_json(SYSTEM_PROMPT, text)
    result = _merge_extraction(text, llm_result)
    return {"complaint": result, "reply": "Complaint parsed successfully. I've extracted the available product and complaint fields and generated an initial risk assessment. Please review the structured form."}


def correction_node(state: ComplaintState):
    existing = state.get("existing") or {}
    message = state["text"]
    deterministic = apply_correction(existing, message)
    llm_payload = {"existing": existing, "instruction": message}
    # complaint_dict() contains Python date objects; make the LangGraph/LLM
    # payload JSON-safe instead of allowing json.dumps() to raise TypeError.
    llm_result = llm_json(CORRECTION_PROMPT, json.dumps(llm_payload, default=str))
    result = deterministic
    if isinstance(llm_result, dict):
        # Only accept values that already exist in the complaint schema.
        for key in deterministic.keys():
            if key in llm_result and llm_result[key] not in (None, "", []):
                result[key] = llm_result[key]
        result = apply_correction(result, message)
    changed = []
    for key in ("batch_number", "affected_quantity", "customer_name", "product_name", "complaint_source", "severity"):
        if result.get(key) != existing.get(key):
            changed.append(key)
    if changed:
        labels = {"batch_number":"Batch / Lot Number","affected_quantity":"Affected Quantity","customer_name":"Customer Name","product_name":"Product Name","complaint_source":"Complaint Source","severity":"Severity"}
        summary = ", ".join(f"{labels[k]} → \"{result.get(k)}\"" for k in changed)
        reply = f"Got it. I have updated {summary} in the form."
    else:
        reply = "I could not identify a structured field change in that instruction. Please specify the field and its new value, for example: batch number is BMX240602."
    return {"complaint": result, "reply": reply}


def build_graph():
    g = StateGraph(ComplaintState)
    g.add_node("extract", extract_node)
    g.add_node("correct", correction_node)
    g.add_conditional_edges(START, lambda s: "correct" if s.get("mode") == "correction" else "extract")
    g.add_edge("extract", END)
    g.add_edge("correct", END)
    return g.compile()

graph = build_graph()
