import React, { useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Bot,
  ChevronDown,
  Paperclip,
  Send,
  ShieldCheck,
  UploadCloud,
  X,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";

import {
  addMessage,
  setBusy,
  setComplaint,
  setError,
  setTools,
  setAudit,
  reset,
} from "./features/complaints/complaintSlice";

import { postJSON, upload, commit, audit } from "./api";

/* ============================================================
   EMPTY COMPLAINT
   ============================================================ */

const empty = {
  complaint_source: "",
  customer_name: "",
  product_name: "",
  product_strength: "",
  batch_number: "",
  affected_quantity: "",
  manufacturing_date: "",
  expiry_date: "",
  complaint_date: "",
  facility: "",
  material_impact: "",
  complaint_type: "",
  description: "",
  severity: "",
  priority: "",
  risk_assessment: "",
  suggested_next_action: "",
  completeness_score: 0,
  missing_fields: [],
  confidence: 0,
  id: null,
  complaint_number: "",
  source: "",
  status: "",
  committed: false,
};

/* ============================================================
   DATE DISPLAY
   ============================================================ */

function displayDate(value) {
  if (!value) return "";

  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [year, month] = value.split("-");

    return new Intl.DateTimeFormat("en", {
      month: "long",
      year: "numeric",
    }).format(new Date(Number(year), Number(month) - 1, 1));
  }

  return value;
}

function buildAssistantResponse(reply, complaintData) {
  if (!complaintData) {
    return reply;
  }

  const lines = ["Complaint parsed successfully.", ""];

  if (complaintData.customer_name) {
    lines.push(`Customer: ${complaintData.customer_name}`);
  }

  if (complaintData.product_name) {
    lines.push(`Product: ${complaintData.product_name}`);
  }

  if (complaintData.product_strength) {
    lines.push(`Strength / Grade: ${complaintData.product_strength}`);
  }

  if (complaintData.batch_number) {
    lines.push(`Batch / Lot: ${complaintData.batch_number}`);
  }

  if (complaintData.affected_quantity) {
    lines.push(`Affected Quantity: ${complaintData.affected_quantity}`);
  }

  if (complaintData.severity) {
    lines.push(`Severity: ${complaintData.severity}`);
  }

  if (complaintData.priority) {
    lines.push(`Priority: ${complaintData.priority}`);
  }

  if (complaintData.completeness_score != null) {
    lines.push(`Completeness: ${complaintData.completeness_score}%`);
  }

  lines.push("");
  lines.push(
    "Please review the structured complaint form and AI risk assessment.",
  );

  return lines.join("\n");
}

/* ============================================================
   MAIN APPLICATION
   ============================================================ */

export default function App() {
  const dispatch = useDispatch();

  const {
    complaint,
    messages,
    busy,
    error,
    tools,
    audit: auditItems,
  } = useSelector((state) => state.complaint);

  const [draft, setDraft] = useState("");
  const [dragging, setDragging] = useState(false);

  const fileRef = useRef(null);

  const c = complaint || empty;

  /* ==========================================================
     HELPERS
     ========================================================== */

  const isReadyToCommit =
    Boolean(complaint) &&
    !c.committed &&
    c.status === "Ready to Commit" &&
    Number(c.completeness_score || 0) >= 80;

  /* ==========================================================
     COMMON API RUNNER
     ========================================================== */

  const run = async (fn, userText = "") => {
    if (busy) return;

    try {
      dispatch(setError(null));

      if (userText) {
        dispatch(
          addMessage({
            role: "user",
            text: userText,
          }),
        );
      }

      dispatch(setBusy(true));

      const res = await fn();

      if (!res || !res.complaint) {
        throw new Error(
          "The server returned an incomplete complaint response.",
        );
      }

      dispatch(setComplaint(res.complaint));

      dispatch(setTools(res.ai_tools || null));

      if (res.reply) {
        dispatch(
          addMessage({
            role: "ai",
            text: buildAssistantResponse(res.reply, res.complaint),
          }),
        );
      }

      if (res.complaint.id) {
        const auditItems = await audit(res.complaint.id);

        dispatch(setAudit(auditItems));
      }
    } catch (e) {
      dispatch(setError(e?.message || "An unexpected error occurred."));
    } finally {
      dispatch(setBusy(false));
    }
  };

  /* ==========================================================
     SEND COPILOT MESSAGE
     ========================================================== */

  const send = () => {
    const text = draft.trim();

    if (!text || busy) return;

    setDraft("");

    if (complaint?.id) {
      run(
        () =>
          postJSON("/api/v1/copilot/message", {
            complaint_id: complaint.id,
            message: text,
          }),
        text,
      );
    } else {
      run(
        () =>
          postJSON("/api/v1/complaints/text", {
            message: text,
          }),
        text,
      );
    }
  };

  /* ==========================================================
     FILE VALIDATION
     ========================================================== */

  const validateFile = (file) => {
    if (!file) {
      return "No file selected.";
    }

    const maxSize = 10 * 1024 * 1024;

    if (file.size > maxSize) {
      return "File size must be 10 MB or smaller.";
    }

    const allowedExtensions = [".pdf", ".docx", ".txt", ".eml"];

    const lowerName = file.name.toLowerCase();

    const supported = allowedExtensions.some((extension) =>
      lowerName.endsWith(extension),
    );

    if (!supported) {
      return (
        "Unsupported file type. " + "Please upload PDF, DOCX, TXT, or EML."
      );
    }

    return null;
  };

  /* ==========================================================
     PROCESS DOCUMENT
     ========================================================== */

  const processFile = (file) => {
    if (!file || busy) return;

    const validationError = validateFile(file);

    if (validationError) {
      dispatch(setError(validationError));

      return;
    }

    run(
      () => upload("/api/v1/complaints/upload", file),
      `Uploaded ${file.name}`,
    );
  };

  /* ==========================================================
     FILE INPUT
     ========================================================== */

  const onFile = (event) => {
    const file = event.target.files?.[0];

    processFile(file);

    event.target.value = "";
  };

  /* ==========================================================
     DRAG / DROP
     ========================================================== */

  const onDragOver = (event) => {
    event.preventDefault();

    if (!busy) {
      setDragging(true);
    }
  };

  const onDragLeave = () => {
    setDragging(false);
  };

  const onDrop = (event) => {
    event.preventDefault();

    setDragging(false);

    if (busy) return;

    const file = event.dataTransfer.files?.[0];

    processFile(file);
  };

  /* ==========================================================
     QMS COMMIT
     ========================================================== */

  const doCommit = async () => {
    if (!complaint?.id) {
      dispatch(setError("No active complaint is available."));

      return;
    }

    if (!isReadyToCommit) {
      dispatch(
        setError(
          "The complaint must be complete and Ready to Commit before it can be committed to the QMS.",
        ),
      );

      return;
    }

    if (busy) return;

    try {
      dispatch(setError(null));
      dispatch(setBusy(true));

      const response = await commit(complaint.id);

      if (!response?.complaint) {
        throw new Error("The QMS commit response was incomplete.");
      }

      dispatch(setComplaint(response.complaint));

      dispatch(
        addMessage({
          role: "ai",
          text: `${response.message} ` + `Ledger ID: ${response.ledger_id}`,
        }),
      );

      const auditItems = await audit(complaint.id);

      dispatch(setAudit(auditItems));
    } catch (e) {
      dispatch(setError(e?.message || "QMS commit failed."));
    } finally {
      dispatch(setBusy(false));
    }
  };

  /* ============================================================
     MANUAL FORM FIELD UPDATE
     ============================================================ */

  const handleFieldChange = (key, value) => {
    if (!complaint) return;

    dispatch(
      setComplaint({
        ...complaint,
        [key]: value,
      }),
    );
  };

  /* ============================================================
     RESET
     ============================================================ */

  const resetForm = () => {
    if (busy) return;

    dispatch(reset());

    setDraft("");
    setDragging(false);

    if (fileRef.current) {
      fileRef.current.value = "";
    }
  };

  /* ============================================================
     RENDER
     ============================================================ */

  return (
    <div className="app-shell">
      {/* ======================================================
          TOP BAR
          ====================================================== */}

      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <Bot size={18} />
          </div>

          <div>
            <div className="brand-title">AIVOA</div>

            <div className="brand-sub">AI QUALITY WORKFLOW</div>
          </div>
        </div>

        <div className="header-actions">
          <span className="status-pill">
            <span className="dot" />
            System Online
          </span>

          <button className="ghost" type="button">
            Pharmaceutical QMS
            <ChevronDown size={15} />
          </button>
        </div>
      </header>

      {/* ======================================================
          MAIN WORKSPACE
          ====================================================== */}

      <main className="workspace">
        {/* ====================================================
            LEFT: COMPLAINT FORM
            ==================================================== */}

        <section className="form-pane">
          {/* FORM HEADER */}

          <div className="form-header">
            <div>
              <div className="eyebrow">
                API &amp; FDF • Customer Complaint Module
              </div>

              <h1>Log Customer Complaint</h1>

              <p>AI-assisted complaint intake and risk assessment</p>
            </div>

            {/* STATUS */}

            <div className="header-status-actions">
              <span
                className={`state-pill ${
                  c.committed
                    ? "committed"
                    : c.status === "Ready to Commit"
                      ? "ready"
                      : ""
                }`}
              >
                {c.committed
                  ? "Committed to QMS"
                  : c.status === "Ready to Commit"
                    ? "Ready to Commit"
                    : complaint
                      ? "Review Required"
                      : "Pending Intake"}
              </span>

              {complaint && (
                <button
                  type="button"
                  className="new-complaint-btn"
                  onClick={resetForm}
                  disabled={busy}
                  title="Start a new complaint"
                >
                  <RotateCcw size={14} />
                  New Complaint
                </button>
              )}
            </div>
          </div>

          {/* ERROR */}

          {error && (
            <div className="error">
              <AlertTriangle size={16} />

              <span>{error}</span>

              <button type="button" onClick={() => dispatch(setError(null))}>
                <X size={15} />
              </button>
            </div>
          )}

          {/* FORM SECTIONS */}

          <div className="sections">
            {/* =================================================
                SECTION 1
                ================================================= */}

            <Section title="1. ORIGIN & CUSTOMER DETAILS">
              <div className="grid two">
                <Field
                  label="Complaint Source"
                  value={c.complaint_source}
                  onChange={(value) =>
                    handleFieldChange("complaint_source", value)
                  }
                />

                <Field
                  label="Customer Name"
                  value={c.customer_name}
                  onChange={(value) =>
                    handleFieldChange("customer_name", value)
                  }
                />
              </div>
            </Section>

            {/* =================================================
                SECTION 2
                ================================================= */}

            <Section title="2. PRODUCT & BATCH IDENTIFICATION">
              <div className="grid two">
                <Field
                  label="Product Name"
                  value={c.product_name}
                  onChange={(value) => handleFieldChange("product_name", value)}
                />

                <Field
                  label="Product Strength / Grade"
                  value={c.product_strength}
                  onChange={(value) =>
                    handleFieldChange("product_strength", value)
                  }
                />

                <Field
                  label="Batch / Lot Number"
                  value={c.batch_number}
                  onChange={(value) => handleFieldChange("batch_number", value)}
                />

                <Field
                  label="Affected Quantity"
                  value={c.affected_quantity}
                  onChange={(value) =>
                    handleFieldChange("affected_quantity", value)
                  }
                />

                <Field
                  label="Manufacturing Date"
                  value={displayDate(c.manufacturing_date)}
                  onChange={(value) =>
                    handleFieldChange("manufacturing_date", value)
                  }
                />

                <Field
                  label="Expiry Date"
                  value={displayDate(c.expiry_date)}
                  onChange={(value) => handleFieldChange("expiry_date", value)}
                />
              </div>
            </Section>

            {/* =================================================
                SECTION 3
                ================================================= */}

            <Section title="3. FACILITY & MATERIAL IMPACT">
              <div className="grid two">
                <Field
                  label="Manufacturing / Receiving Facility"
                  value={c.facility}
                  onChange={(value) => handleFieldChange("facility", value)}
                />

                <Field
                  label="Material / Stock Impact"
                  value={c.material_impact}
                  onChange={(value) =>
                    handleFieldChange("material_impact", value)
                  }
                />
              </div>
            </Section>

            {/* =================================================
                SECTION 4
                ================================================= */}

            <Section title="4. DEFECT ANALYSIS">
              <div className="grid two">
                <Field
                  label="Complaint Category"
                  value={c.complaint_type}
                  onChange={(value) =>
                    handleFieldChange("complaint_type", value)
                  }
                />

                <Field
                  label="Complaint Date"
                  value={displayDate(c.complaint_date)}
                  onChange={(value) =>
                    handleFieldChange("complaint_date", value)
                  }
                />

                <div className="full">
                  <Field
                    label="Complaint Description"
                    value={c.description}
                    onChange={(value) =>
                      handleFieldChange("description", value)
                    }
                    textarea
                  />
                </div>
              </div>
            </Section>

            {/* =================================================
                SECTION 5
                ================================================= */}

            <Section title="5. INITIAL ASSESSMENT & PRIORITY">
              <div className="grid two">
                <Field
                  label="Initial Severity"
                  value={c.severity}
                  onChange={(value) => handleFieldChange("severity", value)}
                />

                <Field
                  label="Priority"
                  value={c.priority}
                  onChange={(value) => handleFieldChange("priority", value)}
                />
              </div>

              {/* ================================================
                  RISK ASSESSMENT
                  ================================================ */}

              <div className="risk-box">
                <div className="risk-title">
                  <ShieldCheck size={17} />
                  AI Copilot Risk Assessment
                  <span className="beta">BETA</span>
                </div>

                <div className="risk-grid">
                  <div>
                    <span className="label">Risk Level</span>

                    <strong>
                      {tools?.risk?.severity || c.severity || "Awaiting AI"}
                    </strong>
                  </div>

                  <div>
                    <span className="label">Confidence</span>

                    <strong>
                      {tools?.risk?.confidence
                        ? `${Math.round(tools.risk.confidence * 100)}%`
                        : "—"}
                    </strong>
                  </div>

                  <div className="wide">
                    <span className="label">Assessment</span>

                    <p>
                      {c.risk_assessment ||
                        tools?.risk?.assessment ||
                        "AI assessment will appear after complaint analysis."}
                    </p>
                  </div>

                  <div className="wide">
                    <span className="label">Suggested Next Action</span>

                    <p>{c.suggested_next_action || "—"}</p>
                  </div>
                </div>
              </div>

              {/* ================================================
                  BONUS AI FEATURES
                  ================================================ */}

              <div className="bonus-row">
                <MiniCard
                  title="Completeness"
                  value={
                    tools?.completeness?.score != null
                      ? `${tools.completeness.score}%`
                      : c.completeness_score
                        ? `${c.completeness_score}%`
                        : "—"
                  }
                  tone={
                    Number(
                      tools?.completeness?.score ?? c.completeness_score ?? 0,
                    ) >= 90
                      ? "good"
                      : "warn"
                  }
                />

                <MiniCard
                  title="Duplicate Scan"
                  value={
                    tools?.duplicates?.length
                      ? "Candidate found"
                      : tools
                        ? "No candidate"
                        : "—"
                  }
                  tone={tools?.duplicates?.length ? "warn" : "good"}
                />

                <MiniCard
                  title="Root Cause"
                  value={tools?.root_cause ? "Suggested" : "—"}
                  tone="neutral"
                />

                <MiniCard
                  title="CAPA"
                  value={tools?.capa ? "Suggested" : "—"}
                  tone="neutral"
                />
              </div>
            </Section>
          </div>

          {/* ====================================================
              BOTTOM ACTION BAR
              ==================================================== */}

          <div className="bottom-bar">
            <button
              className="outline"
              type="button"
              disabled={busy}
              onClick={resetForm}
            >
              <RotateCcw size={16} />
              Reset Form
            </button>

            <button
              className="primary"
              type="button"
              disabled={!isReadyToCommit || busy}
              onClick={doCommit}
              title={
                !complaint
                  ? "Create a complaint first"
                  : !isReadyToCommit
                    ? "Complaint must be Ready to Commit"
                    : "Commit complaint to QMS"
              }
            >
              <CheckCircle2 size={16} />

              {c.committed
                ? "Committed"
                : busy
                  ? "Processing..."
                  : "Commit to QMS Ledger"}
            </button>
          </div>
        </section>

        {/* ====================================================
            RIGHT: AIVOA COPILOT
            ==================================================== */}

        <aside className="copilot-pane">
          {/* COPILOT HEADER */}

          <div className="copilot-head">
            <div className="copilot-title">
              <div className="ai-icon">
                <Bot size={18} />
              </div>

              <div>
                <strong>AIVOA Copilot</strong>

                <span>AI Complaint Intake Assistant</span>
              </div>
            </div>

            <span className="mini-beta">BETA</span>
          </div>

          {/* ==================================================
              DOCUMENT UPLOAD
              ================================================== */}

          <div
            className={`upload-card ${dragging ? "dragging" : ""}`}
            onClick={() => !busy && fileRef.current?.click()}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
          >
            <UploadCloud size={23} />

            <strong>
              {dragging
                ? "Drop complaint document"
                : "Drop complaint document here"}
            </strong>

            <span>
              or <u>click to browse</u>
            </span>

            <small>PDF, DOCX, TXT, EML • Max 10MB</small>

            <input
              ref={fileRef}
              hidden
              type="file"
              accept=".pdf,.docx,.txt,.eml"
              onChange={onFile}
            />
          </div>

          {/* DIVIDER */}

          <div className="divider">
            <span>OR</span>
          </div>

          {/* ASSISTANT STATUS */}

          <div className="chat-label">
            <span>AI ASSISTANT</span>

            <span>{busy ? "PROCESSING" : "READY"}</span>
          </div>

          {/* PROCESSING BAR */}

          {busy && (
            <div className="progress-wrap">
              <div className="progress-bar" />
            </div>
          )}

          {/* ==================================================
              MESSAGE HISTORY
              ================================================== */}

          <div className="messages">
            {messages.length === 0 && (
              <div className="msg ai">
                <div className="msg-icon">
                  <Bot size={14} />
                </div>

                <div className="bubble">
                  Ready to assist with complaint intake. Paste complaint text or
                  upload a complaint document and I will extract the structured
                  fields.
                </div>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`msg ${message.role}`}
              >
                {message.role === "ai" && (
                  <div className="msg-icon">
                    <Bot size={14} />
                  </div>
                )}

                <div className="bubble">{message.text}</div>
              </div>
            ))}
          </div>

          {/* ==================================================
              CHAT INPUT
              ================================================== */}

          <div className="chat-input">
            <button
              type="button"
              title="Attach complaint document"
              disabled={busy}
              onClick={() => fileRef.current?.click()}
            >
              <Paperclip size={17} />
            </button>

            <textarea
              rows="2"
              placeholder={
                complaint
                  ? "Ask me anything about this complaint..."
                  : "Paste complaint text here..."
              }
              value={draft}
              disabled={busy}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();

                  send();
                }
              }}
            />

            <button
              className="send"
              type="button"
              disabled={busy || !draft.trim()}
              onClick={send}
            >
              <Send size={16} />
            </button>
          </div>

          {/* ==================================================
              COPILOT FOOTER
              ================================================== */}

          <div className="copilot-footer">
            AI responses may contain errors. Always verify critical information.
            <br />
            <span>Powered by LangGraph</span>
          </div>

          {/* ==================================================
              COMPLETENESS HINT
              ================================================== */}

          <div className="missing-hint">
            {tools?.completeness?.missing_fields?.length
              ? `Missing / uncertain: ${tools.completeness.missing_fields.join(", ")}`
              : complaint
                ? "All core complaint fields available."
                : "Awaiting complaint information."}
          </div>

          {/* ==================================================
              AUDIT TIMELINE
              ================================================== */}

          <div className="audit">
            <div className="audit-header">
              <span>Audit Timeline</span>

              <span>{auditItems.length} events</span>
            </div>

            {auditItems.length === 0 ? (
              <div className="empty-audit">No events yet.</div>
            ) : (
              auditItems.map((event, index) => (
                <div
                  className="audit-item"
                  key={`${event.event_type}-${index}`}
                >
                  <span className="timeline-dot" />

                  <div>
                    <strong>
                      {String(event.event_type || "").replaceAll("_", " ")}
                    </strong>

                    <p>{event.message}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>
      </main>
    </div>
  );
}

/* ================================================================
   SECTION COMPONENT
   ================================================================ */

function Section({ title, children }) {
  return (
    <section className="section">
      <h2>{title}</h2>

      {children}
    </section>
  );
}

/* ================================================================
   FIELD COMPONENT
   ================================================================ */

function Field({ label, value, onChange, textarea = false, type = "text" }) {
  return (
    <label className={textarea ? "field full" : "field"}>
      <span>{label}</span>

      {textarea ? (
        <textarea
          value={value || ""}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Awaiting AI extraction..."
        />
      ) : (
        <input
          type={type}
          value={value || ""}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Awaiting AI extraction..."
        />
      )}
    </label>
  );
}

/* ================================================================
   MINI AI CARD
   ================================================================ */

function MiniCard({ title, value, tone = "neutral" }) {
  return (
    <div className={`mini-card ${tone}`}>
      <span>{title}</span>

      <strong>{value}</strong>
    </div>
  );
}
