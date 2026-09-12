# AIVOA Advanced Complaint Management System

An AI-powered Customer Complaint Management System for pharmaceutical Quality Management Systems (QMS).

This project converts unstructured customer complaints received through text or uploaded documents into structured complaint records. It also provides AI-assisted risk assessment, complaint completeness checking, duplicate scanning, root-cause and CAPA suggestions, conversational corrections, QMS commitment, and an audit timeline.

---

## Project Overview

Customer complaints in pharmaceutical organizations may arrive as emails, documents, or free-form text. Converting this information into a structured QMS complaint record can require manual effort.

This project provides an AI-assisted complaint intake workflow that:

- Accepts complaint text and uploaded complaint documents
- Extracts structured complaint information
- Populates the complaint form automatically
- Performs AI-assisted risk classification
- Checks complaint completeness
- Performs an initial duplicate complaint scan
- Provides root-cause recommendations
- Provides CAPA recommendations
- Allows conversational corrections through the AIVOA Copilot
- Maintains an audit timeline
- Allows reviewed complaints to be committed to a QMS ledger

This is an internship/demo implementation and is not intended to replace a validated pharmaceutical QMS.

---

# Key Features

## 1. AI Complaint Intake

Users can enter an unstructured complaint directly into the application.

Example:

```text
Apollo Pharmacy reported 12 discolored capsules in Amoxicillin Capsules
500 mg. Batch number AMX240602. Manufacturing date March 2026.
Expiry date February 2028. Please log this complaint.
```

The system extracts fields such as:

- Complaint source
- Customer name
- Product name
- Product strength / grade
- Batch / lot number
- Affected quantity
- Manufacturing date
- Expiry date
- Complaint category
- Severity
- Priority
- Complaint description

---

## 2. Complaint Document Upload

The AIVOA Copilot supports uploaded complaint documents.

Supported formats:

- PDF
- DOCX
- TXT
- EML

Workflow:

```text
Complaint Document
        |
        v
Document Text Extraction
        |
        v
LangGraph Processing
        |
        v
Structured Complaint
        |
        v
Risk Assessment
        |
        v
Complaint Form
```

Production-grade OCR is not implemented because it is not required for this internship assignment.

---

## 3. Conversational Correction

The AIVOA Copilot allows the user to correct extracted information using natural language.

Example:

```text
batch number is BMX240602 and affected quantity is 48 capsules
```

Expected result:

```text
Batch / Lot Number -> BMX240602
Affected Quantity  -> 48 capsules
```

The Copilot confirms the change and the correction is recorded in the audit timeline.

---

## 4. AI Risk Assessment

The system provides an initial AI-assisted risk assessment.

The assessment contains:

- Risk level
- Confidence
- Assessment
- Suggested next action

Example:

```text
Risk Level: Major
Confidence: 91%
```

The AI result is intended as decision support and should be reviewed by the appropriate user before making quality decisions.

---

## 5. Complaint Completeness Check

The system checks whether sufficient complaint information is available.

Example:

```text
Completeness: 100%
```

The completeness result is displayed in the complaint workflow.

---

## 6. Duplicate Complaint Scan

The system performs an initial duplicate/candidate complaint scan.

Example:

```text
Duplicate Scan: Candidate found
```

This is an initial decision-support feature and not a production-grade similarity or matching engine.

---

## 7. Root Cause Recommendation

The application provides an initial root-cause recommendation where applicable.

Example:

```text
Root Cause: Suggested
```

The recommendation is intended to support investigation and is not considered a confirmed root cause.

---

## 8. CAPA Recommendation

The application provides an initial CAPA recommendation where applicable.

Example:

```text
CAPA: Suggested
```

The recommendation requires human review before use in a real quality process.

---

## 9. QMS Ledger Commitment

After reviewing a sufficiently complete complaint, the user can commit the complaint to the QMS ledger.

Workflow:

```text
Review Complaint
        |
        v
Commit to QMS Ledger
        |
        v
Committed to QMS
        |
        v
QMS Ledger ID Generated
```

A QMS commit event is also added to the audit timeline.

---

## 10. Audit Timeline

Important workflow activities are recorded in an audit timeline.

Typical events include:

```text
DOCUMENT UPLOAD
DOCUMENT ANALYZED
AI EXTRACTION
RISK ASSESSMENT
COMPLETENESS CHECK
REVIEW APPROVED
QMS COMMIT
```

This provides visibility into how the complaint moved through the system.

---

# System Architecture

```text
                         AIVOA COMPLAINT MANAGEMENT SYSTEM

┌──────────────────────────────┐
│      User / Complaint        │
│                              │
│  Text / PDF / DOCX / EML     │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       React Frontend         │
│         + Redux              │
│                              │
│ Complaint Form               │
│ AIVOA Copilot                │
│ File Upload                  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       FastAPI Backend        │
│          Python              │
│                              │
│ REST APIs                    │
│ Complaint Processing         │
│ QMS Commit                   │
│ Audit Events                 │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       LangGraph Workflow     │
│                              │
│ Complaint Extraction         │
│ Correction                   │
│ Risk Assessment              │
│ Completeness                 │
│ State / Workflow Control     │
└──────────────┬───────────────┘
               │
        ┌──────┴──────────┐
        ▼                 ▼
┌─────────────────┐ ┌─────────────────┐
│   Groq / LLM    │ │ Deterministic   │
│                 │ │ Fallback Logic  │
│ Extraction      │ │ Validation      │
│ Classification  │ │ Corrections     │
│ Recommendations │ │ Demo Reliability│
└────────┬────────┘ └────────┬────────┘
         └────────────┬──────┘
                      ▼
            ┌──────────────────────┐
            │      PostgreSQL      │
            │                      │
            │ Complaint Records    │
            │ Audit Events         │
            │ Commitment Status    │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │   QMS Workflow       │
            │                      │
            │ Structured Form      │
            │ AI Risk Assessment   │
            │ Completeness         │
            │ Audit Timeline       │
            │ QMS Ledger ID        │
            └──────────────────────┘
```

---

# End-to-End Workflow

The complete request flow is:

```text
User Input
(Text / PDF / DOCX / EML)
        |
        v
React Frontend
        |
        v
Redux State Management
        |
        v
FastAPI REST API
        |
        v
LangGraph Workflow
        |
        +--------------------+
        |                    |
        v                    v
Complaint Extraction    AI Risk Analysis
        |                    |
        +---------+----------+
                  |
                  v
          Validation / Merge
                  |
                  v
        Structured Complaint
                  |
                  v
          Frontend Form
                  |
                  v
             Human Review
                  |
                  v
          QMS Ledger Commit
                  |
                  v
          Audit Timeline
```

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| State Management | Redux Toolkit |
| Build Tool | Vite |
| Backend | Python |
| API Framework | FastAPI |
| AI Workflow | LangGraph |
| LLM | Groq |
| Default Model | `gemma2-9b-it` |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| PDF Parsing | pypdf |
| DOCX Parsing | python-docx |
| Email Parsing | Python `email` package |
| Web Server / Proxy | Nginx |
| Containerization | Docker / Docker Compose |
| UI Font | Inter |

---

# API Endpoints

Main API endpoints:

```text
GET  /api/v1/health

POST /api/v1/complaints/text

POST /api/v1/complaints/upload

POST /api/v1/copilot/message

GET  /api/v1/complaints/{id}

POST /api/v1/complaints/{id}/commit

GET  /api/v1/complaints/{id}/audit
```

The backend handles complaint intake, document processing, AI workflow execution, Copilot corrections, complaint retrieval, QMS commitment, and audit events.

---

# Project Structure

```text
aivoa_advanced_complaint_system_v4/
│
├── README.md
├── docker-compose.yml
├── .env.example
├── example.txt
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core.py
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py
│   │   │   ├── mock_ai.py
│   │   │   └── prompts.py
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── database.py
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── complaint.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── complaint.py
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       └── text_extract.py
│   │
│   └── tests/
│       └── test_mock_ai.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── nginx.conf
│   ├── index.html
│   │
│   └── src/
│       ├── api.js
│       ├── App.jsx
│       ├── main.jsx
│       ├── store.js
│       ├── styles.css
│       │
│       └── features/
│           └── complaints/
│               └── complaintSlice.js
│
├── data/
│   └── sample_complaints/
│       ├── apollo_discoloration.txt
│       ├── metformin_foreign_matter.pdf
│       └── metformin_foreign_matter.txt
│
├── docs/
│   ├── architecture.md
│   └── demo-script.md
│
└── scripts/
    └── smoke_test.py
```

---

# Important Implementation Files

## `backend/app/agents/graph.py`

Contains the LangGraph workflow.

Main responsibilities:

- Complaint extraction
- Correction handling
- Workflow state management
- Combining AI output with deterministic baseline data
- Date validation
- Correction response generation

---

## `backend/app/agents/mock_ai.py`

Provides deterministic complaint-processing and fallback logic.

Main responsibilities:

- Complaint extraction
- Complaint source parsing
- Product parsing
- Product strength parsing
- Batch parsing
- Quantity parsing
- Manufacturing and expiry date parsing
- Complaint category handling
- Conversational corrections
- Demo reliability

---

## `backend/app/main.py`

Contains the FastAPI application and API endpoints.

Responsibilities include:

- Text complaint intake
- Uploaded document intake
- Complaint serialization
- Readiness status
- Complaint retrieval
- Copilot interaction
- QMS commitment
- Audit events

---

## `backend/app/models/complaint.py`

Defines database models for complaint records and audit events.

---

## `backend/app/schemas/complaint.py`

Defines the API request and response schemas.

---

## `backend/app/services/text_extract.py`

Handles text extraction from supported complaint documents.

---

## `frontend/src/App.jsx`

Main application UI.

Responsibilities include:

- Complaint form
- AIVOA Copilot
- Text complaint intake
- Document upload
- Complaint corrections
- AI risk assessment
- Completeness display
- Additional AI recommendation cards
- Audit timeline
- QMS commit

---

## `frontend/src/api.js`

Handles communication between the React frontend and FastAPI backend.

It also provides safe response/error parsing so unexpected backend responses do not directly break frontend JSON handling.

---

## `frontend/src/features/complaints/complaintSlice.js`

Contains Redux state for:

- Complaint
- Copilot messages
- Loading/busy state
- Error state
- AI tool results
- Audit events

---

## `frontend/nginx.conf`

Serves the frontend and proxies `/api/*` requests to the FastAPI backend while running with Docker Compose.

---

# Running the Project

## Prerequisites

Install:

- Docker
- Docker Compose
- Git

Optional:

- Groq API key for the LLM-based AI path

---

# Environment Configuration

Create a local `.env` file based on `.env.example`.

Example:

```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://postgres:postgres@db:5432/aivoa
```

Do not commit the real `.env` file to GitHub.

Only `.env.example` should be committed.

---

# Run with Docker

From the project root:

```bash
docker compose down
docker compose up --build
```

Then open:

```text
Frontend:
http://localhost:5173
```

FastAPI Swagger documentation:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/api/v1/health
```

Keep Docker running while testing the application.

---

# Demo Workflow

## 1. Text Intake

Paste the following complaint:

```text
Apollo Pharmacy reported 12 discolored capsules in Amoxicillin Capsules
500 mg. Batch number AMX240602. Manufacturing date March 2026.
Expiry date February 2028. Please log this complaint.
```

Expected core fields:

```text
Complaint Source: Pharmacy
Customer: Apollo Pharmacy
Product: Amoxicillin Capsules
Strength: 500 mg
Batch: AMX240602
Quantity: 12 discolored capsules
Manufacturing Date: March 2026
Expiry Date: February 2028
Complaint Category: Product Defect - Discoloration
Severity: Major
Priority: High
```

---

## 2. Conversational Correction

Send:

```text
batch number is BMX240602 and affected quantity is 48 capsules
```

Expected result:

```text
Batch / Lot Number -> BMX240602
Affected Quantity  -> 48 capsules
```

The Copilot should confirm the correction and the audit timeline should record the user correction.

---

## 3. PDF Workflow

Upload:

```text
data/sample_complaints/metformin_foreign_matter.pdf
```

Expected result:

```text
Product:
Metformin Hydrochloride API

Grade:
IP/BP Grade

Batch:
CHG260712A

Quantity:
50 kg (2 HDPE Drum)

Complaint Category:
Foreign Matter Contamination

Severity:
Critical

Priority:
Urgent
```

Additional AI result cards should also be displayed where applicable.

---

## 4. QMS Commit

After reviewing the complaint:

```text
Commit to QMS Ledger
```

Expected result:

```text
Committed to QMS
```

The application generates a QMS ledger identifier and records the commitment in the audit timeline.

---

# Sample Complaint Data

Sample complaint files are available under:

```text
data/sample_complaints/
```

Included files:

```text
apollo_discoloration.txt
metformin_foreign_matter.txt
metformin_foreign_matter.pdf
```

These files can be used to reproduce the demonstrated workflows.

---

# Audit Trail

A typical successful workflow produces audit events similar to:

```text
DOCUMENT UPLOAD
        |
        v
DOCUMENT ANALYZED
        |
        v
AI EXTRACTION
        |
        v
RISK ASSESSMENT
        |
        v
COMPLETENESS CHECK
        |
        v
REVIEW APPROVED
        |
        v
QMS COMMIT
```

The audit trail makes the processing history visible to the user.

---

# Reliability and Fallback Design

The project includes deterministic complaint-processing logic in addition to the LLM-based workflow.

The fallback logic helps keep the demonstration usable when an LLM API key is unavailable and also provides deterministic handling for important structured fields.

This includes:

- Complaint field extraction
- Batch parsing
- Quantity parsing
- Date handling
- Conversational corrections
- Structured field consistency

The fallback layer is intended for demonstration reliability and should not be interpreted as a replacement for production AI validation.

---

# Docker Architecture

The application can be run as a multi-service Docker Compose setup:

```text
┌────────────────────┐
│ React Frontend     │
└─────────┬──────────┘
          |
          v
┌────────────────────┐
│ Nginx Proxy        │
└─────────┬──────────┘
          |
          v
┌────────────────────┐
│ FastAPI Backend    │
└─────────┬──────────┘
          |
          v
┌────────────────────┐
│ LangGraph / AI     │
└─────────┬──────────┘
          |
          v
┌────────────────────┐
│ PostgreSQL         │
└────────────────────┘
```

---

# Limitations

This project is an internship/demo implementation.

Current limitations include:

- Production-grade OCR is not implemented.
- AI recommendations are decision-support only.
- Root-cause suggestions are not confirmed investigation results.
- CAPA recommendations require human review.
- Duplicate detection is an initial candidate scan.
- The QMS ledger is synthetic/demo functionality.
- The application is not validated for regulated pharmaceutical production use.

Critical quality decisions should always be reviewed by the appropriate human quality professional.

---

## Demo Video

Watch the complete AIVOA Complaint Management System demonstration:

**[▶️ Watch AIVOA Demo Video](https://drive.google.com/file/d/1Vp8FijTnlGiumu4sLDKg9mmSrxYpVf/view?usp=sharing)**

The demo covers:

- Text complaint intake
- AI complaint extraction
- Structured complaint form population
- AI risk assessment
- Copilot correction
- PDF complaint upload
- Completeness and AI recommendation features
- QMS ledger commitment
- Audit timeline
- Architecture and code walkthrough

# Documentation

Architecture documentation:

```text
docs/architecture.md
```

Demo narration/script:

```text
docs/demo-script.md
```

---

# Security

Never commit credentials or secrets to GitHub.

Do not upload:

```text
.env
API keys
Passwords
Private credentials
Local database files
```

Use:

```text
.env.example
```

to document required environment variables without exposing secrets.

---

# GitHub Submission Checklist

Before submitting the repository, verify:

```text
[ ] README.md is present
[ ] .gitignore is present
[ ] .env is NOT committed
[ ] .env.example is present
[ ] Backend source code is present
[ ] Frontend source code is present
[ ] docker-compose.yml is present
[ ] Sample complaint files are present
[ ] Architecture documentation is present
[ ] Demo script is present
[ ] Project starts successfully with Docker
[ ] Frontend opens successfully
[ ] FastAPI /docs opens successfully
[ ] Text complaint workflow works
[ ] PDF workflow works
[ ] Copilot correction works
[ ] QMS commit works
[ ] Audit timeline works
```

---

# Assignment Alignment

This project follows the requested AIVOA implementation direction:

- React + Redux frontend
- Python + FastAPI backend
- LangGraph AI workflow
- Groq LLM integration
- PostgreSQL database
- Customer complaint extraction
- Complaint risk classification
- Complaint completeness checking
- Duplicate complaint scanning
- Root-cause recommendation
- CAPA recommendation
- Complaint document upload
- Conversational correction
- QMS commitment
- Audit timeline

---

# Conclusion

AIVOA Advanced Complaint Management System demonstrates an end-to-end AI-assisted complaint intake workflow for a pharmaceutical QMS environment.

The implementation combines:

```text
React
+
Redux Toolkit
+
FastAPI
+
LangGraph
+
Groq
+
PostgreSQL
+
Docker
```

to transform unstructured customer complaints into structured, reviewable and auditable complaint records.

The system is designed to demonstrate the complete workflow from user input through AI processing, structured complaint generation, risk assessment, human review and QMS commitment.
