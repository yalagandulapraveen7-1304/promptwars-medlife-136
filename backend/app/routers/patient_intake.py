from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from app.models.patient_intake import (
    PatientIntakeSubmission,
    PatientIntakeResponse,
    NominationRequest,
    NominationResponse,
    IntakePreFillBundle
)
from app.database import (
    get_patient_intake,
    save_patient_intake_db,
    submit_patient_nomination_db,
    get_intake_prefill_bundle
)

router = APIRouter(prefix="/api/intake", tags=["Patient Intake & Nomination"])

@router.get("/prefill", response_model=IntakePreFillBundle)
def get_intake_prefill(
    source: str = Query("wristband", description="Source of prefill: 'wristband' for barcode scan, 'epic' for FHIR sync")
):
    """
    Rapid Clinical Pre-fill (Module 3).
    Simulates instantaneous wristband barcode scan or Epic / Cerner EHR sync
    matched against the Master Patient Index (MPI).
    """
    data = get_intake_prefill_bundle(source=source.lower())
    return data

@router.get("/{patient_mrn}")
def get_intake_details(patient_mrn: str):
    """
    Fetch stored patient intake demographic and admission details by MRN.
    """
    record = get_patient_intake(patient_mrn)
    if not record:
        raise HTTPException(status_code=404, detail=f"Intake record for patient {patient_mrn} not found.")
    return record

@router.post("/submit", response_model=PatientIntakeResponse)
def submit_patient_intake(submission: PatientIntakeSubmission):
    """
    Submit completed Patient Demographic & Clinical Intake (Section A through H).
    Enqueues patient into Doctor Dashboard triage queue, increments admissions KPI,
    and commits verified demographics to master registry.
    """
    mrn, session_id, _ = save_patient_intake_db(submission.model_dump(), is_draft=False)
    now_str = datetime.now().strftime("%d %b %Y %H:%M EST")
    return PatientIntakeResponse(
        success=True,
        mrn=mrn,
        session_id=session_id,
        status="SUBMITTED",
        message=f"Patient {mrn} registered and enqueued for Doctor Triage.",
        triage_enqueued=True,
        admitted_at=now_str
    )

@router.post("/save-draft", response_model=PatientIntakeResponse)
def save_intake_draft(submission: PatientIntakeSubmission):
    """
    Save in-progress demographic intake draft without finalizing triage admission.
    """
    mrn, session_id, _ = save_patient_intake_db(submission.model_dump(), is_draft=True)
    now_str = datetime.now().strftime("%d %b %Y %H:%M EST")
    return PatientIntakeResponse(
        success=True,
        mrn=mrn,
        session_id=session_id,
        status="DRAFT",
        message=f"Intake draft for {mrn} saved successfully.",
        triage_enqueued=False,
        admitted_at=now_str
    )

@router.post("/nominate", response_model=NominationResponse)
def nominate_patient(nomination: NominationRequest):
    """
    Nominate patient for AI-assisted multi-source ingestion, specialized care pathways,
    and complex conflict reconciliation.
    """
    nom_id, mrn, score, now_iso = submit_patient_nomination_db(nomination.model_dump())
    return NominationResponse(
        success=True,
        nomination_id=nom_id,
        patient_mrn=mrn,
        status="PROCESSING",
        readiness_score=score,
        message=f"Nomination #{nom_id} approved by {nomination.signoff_doctor} and dispatched to MedLens extraction engine.",
        timestamp=now_iso
    )

@router.get("/readiness-score/{patient_mrn}")
def get_readiness_score(patient_mrn: str):
    """
    Retrieve document readability score, MPI alignment status, and OCR readiness checklist.
    """
    return {
        "patient_mrn": patient_mrn,
        "readiness_score": 94,
        "document_clarity": "High semantic clarity across 3 source records",
        "mpi_matched": True,
        "tabular_labs_detected": 14,
        "unresolved_date_overlaps": 1,
        "engine_version": "v4.2"
    }
