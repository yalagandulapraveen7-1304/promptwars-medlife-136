# Product Requirements Document (PRD): MedLens Clinical Intelligence Platform

**Document Version:** 1.0.0  
**Status:** Approved for Implementation  
**Product Owner:** Clinical Product & AI Systems Architecture  
**Compliance Standard:** Designed with privacy and security best practices (AES-256 encryption, immutable audit logging, NIST guidelines, FHIR R4 interoperability)  

---

## 1. Executive Summary & Vision

### 1.1 Problem Statement
Modern clinical workflows suffer from severe data fragmentation. Clinicians routinely juggle disparate Electronic Health Record (EHR) systems (Epic, Cerner/Oracle Health), scanned unstructured paper discharge summaries, external laboratory PDFs, and handwritten triage questionnaires. This fragmentation creates:
- **Cognitive Overload:** Clinicians spend up to 40% of their day hunting across PDF attachments and EHR tabs to assemble a cohesive clinical picture.
- **Diagnostic Blindspots & Latent Risk:** Vital drug-allergy interactions and historical contraindications buried in external discharge notes are frequently missed during rapid bedside intake.
- **AI Hallucination & Loss of Trust:** Generic generative AI solutions hallucinate clinical reference ranges or summarize patient records without accountable source citations, making them unviable for clinical decision support.

### 1.2 Product Vision
**MedLens** is an AI-assisted clinical intelligence and human-in-the-loop EHR reconciliation platform. MedLens ingest fragmented, multi-source patient records and transforms them into a structured, traceable, and reviewable patient record. Every extracted parameter is bound to an auditable source citation, and clinical reasoning is governed by transparent evidence viewing rather than autonomous decisions.

---

## 2. Core Personas & User Journeys

| Persona | Role & Context | Primary Jobs to be Done (JTBD) | Key Pain Points |
| :--- | :--- | :--- | :--- |
| **Dr. Sarah Jenkins, MD** | Attending Cardiologist & Clinical Lead | Triage inpatient queues, review lab anomalies, verify discrepancy alerts, and approve clinical order sets. | Visual fatigue from legacy EHR interfaces; high risk of missing buried allergen contraindications. |
| **Nurse Kelly, BSN, RN** | Triage & Inpatient Intake Nurse | Collect patient demographics, conduct structured pre-fill intake, capture photo scans of physical wristbands or outside records. | Redundant data entry across disconnected systems; slow manual verification of payer eligibility. |
| **Chief Medical Information Officer (CMIO)** | Health System Governance & Compliance | Ensure zero ungrounded clinical AI hallucinations, enforce rigorous privacy, security, and audit logging standards, monitor OCR extraction error rates. | Lack of explainability in black-box clinical algorithms; potential regulatory liability. |

---

## 3. Product Architecture & Core Modules

MedLens is organized into 8 interconnected architectural modules:

### Module 1: Master Patient Identity & Intake Routing (MPI)
- **FHIR Interoperability:** Real-time bidirectional synchronization with Epic FHIR and Cerner Millenium via standard SMART on FHIR protocols.
- **NIST Level-3 Identity Matching:** Automatic reconciliation of incoming patient records with Master Patient Index records based on legal name, date of birth, masked SSN, and national MPI hashes.
- **Department Routing:** Automated assignment to designated inpatient wards, beds, and attending provider teams (e.g., *Cardiology & Acute Vascular — Bed 412-B*).

### Module 2: Structured Intake Engine (Sections A–H)
A progressive 8-stage clinical intake workflow:
1. **Section A (Demographics):** Legal identity, contact preferences, Durable Power of Attorney (DPOA) advance directive logging, payer real-time 270/271 EDI eligibility validation.
2. **Section B (Chief Complaint):** Categorized onset, severity, and natural language clinical memos.
3. **Section C (Medical History):** Prior diagnoses, surgical episodes, and family predispositions.
4. **Section D (Active Medications):** Dosage, frequency, adherence status, and prescribing provider.
5. **Section E (Allergies & Reactions):** Severity classifications (Mild, Moderate, Severe Anaphylaxis) with provenance tags.
6. **Section F (Source Documents):** Multi-format ingestion drop-zone.
7. **Section G (Clinical Notes & Observations):** Bedside physical findings.
8. **Section H (Physician Sign-Off):** Cryptographic physician sign-off.

### Module 3: Document Processing & Table Detection Pipeline
- **Multi-Format Ingest:** Secure upload for PDF, scanned JPG/PNG, DICOM metadata snapshots, and CCDA XML dossiers up to 50 MB per file.
- **Intelligent OCR & Table Extraction:** Convolutional layout analysis preserving complex tabular laboratory structures (confidence score target > 95%).
- **De-identification Engine:** Client-side de-identification conforming to privacy and de-identification best practices before processing non-EHR document payloads.

### Module 4: Structured Medical Record & Reference Range Integrity
- **Zero-Hallucination Range Policy:** Clinical reference ranges must be extracted directly from the specimen source lab report. If omitted in the original report, the system explicitly marks the status as **`NOT DETERMINED FROM SOURCE`**—it strictly forbids inferring default biological reference bounds.
- **Status Flagging:** Real-time categorical classification (`LOW`, `NORMAL`, `HIGH`, `CRITICAL OUT-OF-RANGE`).
- **Historical Delta Tracking:** Inline comparative visualization showing previous vs. current values (e.g., $12.1 \rightarrow 10.2\text{ g/dL} \downarrow 1.9$) with divergence sparklines.

### Module 5: Cross-Document Conflict & Discrepancy Engine
- **Early-Watch Contraindication Scanner:** Cross-references self-reported intake statements against historical scanned hospital discharge summaries and external EHR transfers.
- **Mandatory Bedside Verification Gates:** When a critical conflict is identified (e.g., self-reported *"No Known Drug Allergies"* vs. historical discharge note documenting *"Cutaneous rash & hives secondary to Ampicillin/Sulbactam"*), MedLens places a mandatory clinical safety hold requiring human physical re-verification before order sets can be unlocked.

### Module 6: Doctor AI Copilot & Evidence Viewer
- **Side-by-Side Dual Pane:** Left pane displays the interactive structured patient record; right pane renders the original PDF/document with bounding-box highlights anchored to line citations (e.g., `Citation: LabCorp CBC, Page 2, Line 14`).
- **Human-in-the-Loop Actions:** Every AI-suggested extraction or clinical insight includes explicit `[Verify]`, `[Edit / Override]`, or `[Reject]` controls.
- **Grounded Copilot Queries:** In-context conversational engine answering shift-specific queries strictly restricted to verified document citations.

### Module 7: Clinical Triage & Provider Dashboard
- **Urgency Scoring & Prioritization:** Automated categorization by clinical priority:
  - *Acute Triage (< 2h fast-track SLA)*
  - *Priority Review (24h SLA)*
  - *Routine Processing (72h SLA)*
- **Shift Handover & Batch Management:** Live inpatient roster tracking, pending laboratory sign-offs, and batch sign-off capabilities for attending physicians.

### Module 8: Security, Provenance & Audit Trails
- **Cryptographic Provenance:** Every datum in the system is linked to an immutable audit record containing:
  - Origin source document and page number.
  - Ingestion timestamp and AI model confidence score.
  - Name, NPI, and timestamp of the verifying clinician.
- **Enterprise Security & Privacy Controls:** Full data-at-rest (AES-256) and data-in-transit (TLS 1.3) encryption with comprehensive audit trail exports.

---

## 4. Visual Design System & UX Standards

**Design System Identifier:** `Clinical Clarity & Care` (`LIGHT` mode)
- **Primary Color:** `#0284c7` (Clinical Sapphire)
- **Surfaces:** Soothing clinical off-white (`#f8f9ff`) to soft container low (`#eff4ff`), engineered to reduce glare and visual fatigue during 12-hour hospital shifts.
- **Typography:** Humanist sans-serif system (*Plus Jakarta Sans* for headings and badges; *Inter / Roboto* for high-density tabular and numerical lab readouts).
- **Component Geometry:** 8px border radius (`ROUND_EIGHT`), subtle borders (`#ccdbf3`), and tactile button states with integrated keyboard shortcuts (`⌘ + Enter`).

---

## 5. Functional & Non-Functional Requirements

### 5.1 Functional Requirements
1. **MPI Reconciliation:** Match candidate patient profiles with an existing Master Patient Index in $\le 800\text{ms}$ with $>99.2\%$ confidence.
2. **Tabular OCR Precision:** Lab table column and row alignment must maintain $\ge 98\%$ structural fidelity across standard commercial lab vendors (LabCorp, Quest, Epic MyChart PDFs).
3. **Discrepancy Surfacing:** Allergen and medication contradictions across multi-source documents must trigger high-severity alert banners within $\le 3\text{ seconds}$ of ingestion.
4. **Traceable Verification:** Clicking any lab parameter or copilot response must immediately open the corresponding source document scrolled and centered on the highlighted bounding box.

### 5.2 Non-Functional Requirements
1. **Performance:** Page load under standard hospital broadband $\le 1.2\text{s}$; full OCR and structured table rendering $\le 4.5\text{s}$ per 10-page dossier.
2. **Security & Privacy:** Privacy and security controls aligned with industry best practices; no patient Health Information (PHI) used for foundational model retraining; role-based access control (RBAC).
3. **Availability & Reliability:** 99.99% uptime with offline local caching for bedside vital entries.
4. **Accessibility:** WCAG 2.1 AA compliant contrast ratios across all clinical alerts, status flags, and form input states.

---

## 6. Success Metrics & KPIs

| Metric | Baseline (Legacy EHR) | Target (MedLens Q1) | Business & Clinical Impact |
| :--- | :--- | :--- | :--- |
| **Physician Intake Review Time** | 18.5 mins / patient | $\le 4.2\text{ mins}$ / patient | **77% reduction** in intake review time; mitigates physician burnout. |
| **Allergy & Contraindication Catch Rate** | 89.4% (manual check) | $\ge 99.8\%$ (AI + Human Gate) | Drastic reduction in preventable adverse drug events (ADEs). |
| **Lab Value Verification Accuracy** | 94.0% | $99.9\%$ with source bounding box | Eliminates manual transcription and EHR entry errors. |
| **Clinician Ergonomics / SUS Score** | 46 / 100 (Legacy EHR) | $\ge 88 / 100$ | Exceptional clinician adoption and shift comfort. |

---

## 7. Release Roadmap

- **Phase 1 (Delivered):** Core Desktop & Mobile Design System, Doctor Triage Dashboard, Patient Intake Nomination, Structured Record with Reference Range Awareness, and Section A Demographic Intake.
- **Phase 2 (Next Sprint):** Interactive Split-Pane Side-by-Side OCR Evidence Viewer with real-time bounding box inspection and live conflict reconciliation flow.
- **Phase 3:** Epic & Cerner FHIR bidirectional write-back gateway, custom hospital formulary ingestion, and voice-to-structured bedside intake.