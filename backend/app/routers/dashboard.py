from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models.dashboard import (
    DashboardOverviewResponse, ClinicianProfile, KPIMetrics, PipelineStatus,
    FilterCounts, TriagePatient, VerifyLabResponse, ResolveConflictRequest,
    BatchSignOffResponse, EHRSyncResponse, FlagNurseRequest, FlagNurseResponse,
    LabOverrideRequest, LabOverrideResponse
)
from app.database import (
    get_overview_data, get_dashboard_filter_counts, get_triage_patients, verify_lab_result,
    resolve_patient_conflict, batch_sign_off_pending, trigger_ehr_sync,
    flag_for_nurse, get_nurse_flags, override_dashboard_lab
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview():
    """Retrieve clinician profile, active shift parameters, top KPI metric counters, OCR pipeline status, and filter badge counts."""
    clinician_dict, kpi_dict, pipe_dict, filter_counts = get_overview_data()
    return DashboardOverviewResponse(
        clinician=ClinicianProfile(**clinician_dict),
        metrics=KPIMetrics(**kpi_dict),
        pipeline=PipelineStatus(**pipe_dict),
        filter_counts=FilterCounts(**filter_counts)
    )

@router.get("/filter-counts", response_model=FilterCounts)
def get_filter_counts():
    """Get dynamic counts for quick pill filters directly from the database."""
    counts = get_dashboard_filter_counts()
    return FilterCounts(**counts)

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
    _, _, pipe_dict, _ = get_overview_data()
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

@router.post("/flag-nurse/{patient_mrn}", response_model=FlagNurseResponse)
def dispatch_nurse_flag(patient_mrn: str, payload: Optional[FlagNurseRequest] = None):
    """
    Dispatch an urgent clinical bedside instruction / allergy validation task to the assigned on-duty nurse.
    Persists flag in database and records clinician signature in HIPAA audit log.
    """
    p_data = payload or FlagNurseRequest()
    res = flag_for_nurse(
        patient_mrn=patient_mrn,
        nurse_name=p_data.nurse_name or "Nurse Kelly, RN",
        reason=p_data.reason or "Bedside allergy re-check & scratch test protocol",
        priority=p_data.priority or "URGENT",
        created_by="Dr. Sarah Jenkins, MD"
    )
    return FlagNurseResponse(**res)

@router.get("/nurse-flags")
def list_all_nurse_flags():
    """List all active or historical nurse task flags across the cardiology and acute care ward."""
    return get_nurse_flags()

@router.get("/nurse-flags/{patient_mrn}")
def get_patient_nurse_flags(patient_mrn: str):
    """Retrieve active nurse task flags specific to an individual patient."""
    return get_nurse_flags(patient_mrn=patient_mrn)

@router.post("/override-lab/{patient_mrn}/{test_code}", response_model=LabOverrideResponse)
def override_lab(patient_mrn: str, test_code: str, payload: LabOverrideRequest):
    """
    Clinician manual correction and override of an extracted laboratory biomarker from the triage dashboard.
    Commits new value, adjusts status flag, and records reason in the audit log.
    """
    updated = override_dashboard_lab(
        patient_mrn=patient_mrn,
        test_code=test_code,
        result_value=payload.result_value,
        unit=payload.unit,
        reference_interval=payload.reference_interval,
        status=payload.status,
        reason=payload.override_reason,
        clinician_name="Dr. Sarah Jenkins, MD"
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Lab test {test_code} for patient {patient_mrn} could not be updated.")

    return LabOverrideResponse(
        success=True,
        message=f"Laboratory test {test_code} successfully overridden to {payload.result_value} ({payload.status}).",
        updated_lab=updated
    )

