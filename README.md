# AIVOA Advanced Complaint Management System

An AI-powered Customer Complaint Management System for pharmaceutical Quality Management Systems (QMS), inspired by the workflow demonstrated in the AIVOA complaint module.

The system converts unstructured customer complaints from text or uploaded documents into structured complaint records, performs AI-assisted risk assessment and completeness analysis, supports conversational corrections through the Copilot, and allows reviewed complaints to be committed to a QMS ledger with an audit trail.

---

## Project Overview

In pharmaceutical complaint management, customer complaints may arrive as emails, documents, or free-form text. Manually transferring this information into a structured QMS form can be time-consuming and error-prone.

This project addresses that workflow by providing an AI-assisted complaint intake system that:

1. Accepts complaint text or complaint documents.
2. Extracts important complaint fields.
3. Populates the structured complaint form.
4. Performs AI-assisted risk classification.
5. Checks complaint completeness.
6. Provides duplicate, root-cause and CAPA suggestions.
7. Allows users to correct extracted information through the Copilot.
8. Maintains an audit timeline.
9. Commits reviewed complaints to a QMS ledger.

The implementation is designed as an internship/demo system and is not intended to replace a validated pharmaceutical QMS.

---

# Key Features

## 1. AI Complaint Intake

Users can enter an unstructured complaint directly through the application.

Example:

```text
Apollo Pharmacy reported 12 discolored capsules in Amoxicillin Capsules
500 mg. Batch number AMX240602. Manufacturing date March 2026.
Expiry date February 2028. Please log this complaint.
