# AIVOA Advanced Complaint AI — Demo-Parallel Version 3

This version focuses first on **functional parity with the supplied AIVOA complaint demo**: text/email intake, structured form population, correction through Copilot, PDF/DOCX/TXT/EML upload, initial risk assessment, completeness, duplicate scan, root-cause/CAPA suggestions, QMS commit, and audit timeline.

## Stack

- Frontend: React + Redux Toolkit + Vite
- Backend: Python + FastAPI
- AI workflow: LangGraph
- LLM: Groq (`gemma2-9b-it` by default, configurable)
- Database: PostgreSQL / SQLAlchemy
- PDF: pypdf
- DOCX: python-docx
- EML: Python email parser
- UI font: Inter

## Run with Docker (recommended)

From the project root:

```bash
docker compose down
# If migrating a very old local database and you do not need its records:
# docker compose down -v

docker compose up --build
```

Open:

- Frontend: http://localhost:5173
- FastAPI docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

Keep Docker running while you test.

## Demo-parity test

### 1. Text intake

Paste:

```text
Apollo Pharmacy reported 12 discolored capsules in Amoxicillin Capsules 500 mg. Batch number AMX240602. Manufacturing date March 2026. Expiry date February 2028. Please log this complaint.
```

Expected core fields:

- Complaint Source: Pharmacy
- Customer: Apollo Pharmacy
- Product: Amoxicillin Capsules
- Strength: 500 mg
- Batch: AMX240602
- Quantity: 12 discolored capsules
- Manufacturing: March 2026
- Expiry: February 2028
- Complaint Category: Product Defect - Discoloration
- Severity: Major
- Priority: High

### 2. Conversational correction

Send:

```text
batch number is BMX240602 and affected quantity is 48 capsules
```

Expected:

- AI confirmation message appears
- Batch / Lot Number changes to BMX240602
- Affected Quantity changes to 48 capsules
- Audit timeline records the user correction

### 3. PDF workflow

Upload:

`data/sample_complaints/metformin_foreign_matter.pdf`

Expected:

- Metformin Hydrochloride API complaint extracted
- Batch, quantity, dates and complaint category populated
- Critical risk recommendation displayed
- Completeness / duplicate / root-cause / CAPA cards populated

### 4. QMS commit

When the core complaint is sufficiently complete, click **Commit to QMS Ledger**. The status changes to **Committed to QMS** and a QMS commit event is added to the audit timeline.

## Where the important fixes live

### Backend

`backend/app/agents/mock_ai.py`
- Complete deterministic extraction for the demo inputs
- Correct manufacturing/expiry ordering
- Natural-language quantity parsing
- Complaint source/product/batch parsing
- Conversational correction parsing

`backend/app/agents/graph.py`
- LangGraph extraction/correction nodes
- Safe merge between Groq output and deterministic baseline
- Prevents malformed/reversed date data from corrupting the demo form
- Generates explicit correction replies

`backend/app/main.py`
- Complaint serialization
- Readiness status (`Ready to Commit`)
- Additive migration for `facility` and `material_impact`
- Audit/QMS endpoints

`backend/app/models/complaint.py`
- Adds `facility` and `material_impact`

`backend/app/schemas/complaint.py`
- Adds the same structured fields to API schemas

### Frontend

`frontend/src/api.js`
- Safe JSON/error parsing so HTML/internal-server responses do not cause `Unexpected token '<'`/`Unexpected token 'I'` failures

`frontend/src/App.jsx`
- Demo-parallel sections
- Month/year display for manufacturing and expiry dates
- Facility/material impact section
- Defect analysis section
- Drag-and-drop file upload
- Correction response rendering
- Completeness hint and LangGraph footer

`frontend/src/styles.css`
- Ready-to-commit state
- Drag/drop visual state
- Completeness hint styling

`frontend/nginx.conf`
- Proxies `/api/*` to the FastAPI backend in Docker

## Notes

Production-grade OCR is intentionally not implemented; the assignment explicitly says it is not required. This project is an internship/demo implementation rather than a validated pharmaceutical QMS.


## V4 correction
- Fixed Copilot correction crash caused by `date` objects being passed directly to `json.dumps()`. The correction payload is now serialized with `default=str`.
- Removed fixed Docker `container_name` values so V3/V4 and other Compose projects do not collide on `aivoa-*` container names.

### Clean restart
```powershell
docker compose down
docker rm -f aivoa-postgres aivoa-backend aivoa-frontend 2>$null
docker compose up --build
```
Do not use `docker compose down -v` unless you intentionally want to delete the project database volume.
