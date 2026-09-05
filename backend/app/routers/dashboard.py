from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models.dashboard import (
    DashboardOverviewResponse, ClinicianProfile, KPIMetrics, PipelineStatus,
    TriagePatient, VerifyLabResponse, ResolveConflictRequest,
    BatchSignOffResponse, EHRSyncResponse
)
from app.database import (
    get_overview_data, get_triage_patients, verify_lab_result,
    resolve_patient_conflict, batch_sign_off_pending, trigger_ehr_sync
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview():
    """Retrieve clinician profile, active shift parameters, top KPI metric counters, and OCR pipeline status."""
    clinician_dict, kpi_dict, pipe_dict = get_overview_data()
    return DashboardOverviewResponse(
        clinician=ClinicianProfile(**clinician_dict),
        metrics=KPIMetrics(**kpi_dict),
        pipeline=PipelineStatus(**pipe_dict)
    )

@router.get("/triage-queue", response_model=List[TriagePatient])
def get_triage_queue(
    filter: str = Query("all", description="Filter by: all | out_of_range | conflicts | pending"),
    q: Optional[str] = Query(None, description="Search by patient name, MRN, or lab code")
):
    """Retrieve inpatient priority triage queue with multi-source labs, conflict alerts, and filtering."""
    patients_data = get_triage_patients(filter_type=filter, query=q)
    return [TriagePatient(**p) for p in patients_data]

@router.get("/pipeline-stream", response_model=PipelineStatus)
def get_pipeline_stream():
    """Live telemetry stream for OCR tabular document processing and table detection."""
    _, _, pipe_dict = get_overview_data()
    return PipelineStatus(**pipe_dict)

@router.post("/verify-lab/{patient_mrn}/{test_code}", response_model=VerifyLabResponse)
def verify_lab(patient_mrn: str, test_code: str):
    """Doctor verifies an extracted lab value, committing cryptographic provenance and updating pending KPI counters."""
    updated_lab, pending_count = verify_lab_result(patient_mrn=patient_mrn, test_code=test_code)
    if not updated_lab:
        raise HTTPException(status_code=404, detail=f"Lab {test_code} for patient {patient_mrn} not found.")

    return VerifyLabResponse(
        success=True,
        message=f"Lab {test_code} verified by Dr. Sarah Jenkins, MD.",
        lab=updated_lab,
        updated_pending_count=pending_count
    )

@router.post("/resolve-conflict/{patient_mrn}")
def resolve_conflict(patient_mrn: str, payload: ResolveConflictRequest):
    """Enforce mandatory bedside allergy scratch-test gate or confirm clinical override."""
    success, detail = resolve_patient_conflict(patient_mrn=patient_mrn, action=payload.action)
    return {
        "success": success,
        "patient_mrn": patient_mrn,
        "action": payload.action,
        "detail": detail
    }

@router.post("/batch-signoff", response_model=BatchSignOffResponse)
def batch_sign_off():
    """Batch approve all verified labs and complete pending doctor reviews across the active ward."""
    count = batch_sign_off_pending()
    return BatchSignOffResponse(
        success=True,
        count_verified=count,
        message=f"Batch signed off {count} clinical items successfully.",
        remaining_pending=0
    )

@router.post("/sync-ehr", response_model=EHRSyncResponse)
def sync_ehr():
    """Trigger real-time bidirectional FHIR synchronization with St. Jude Epic / Cerner EHR."""
    new_time = trigger_ehr_sync()
    return EHRSyncResponse(
        success=True,
        sync_time=new_time,
        patients_synced=128,
        labs_updated=7,
        message="Epic FHIR and Cerner Millenium synchronization completed."
    )
