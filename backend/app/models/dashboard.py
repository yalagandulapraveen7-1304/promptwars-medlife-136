from typing import List, Optional
from pydantic import BaseModel, Field

class ClinicianProfile(BaseModel):
    name: str = "Dr. Sarah Jenkins, MD"
    role: str = "Attending Cardiologist & Clinical Lead"
    license_num: str = "MED-88192"
    hospital: str = "St. Jude Health Clinic"
    ward: str = "Cardiology Unit 4B"
    shift: str = "07:00 – 19:00 EST"
    avatar_url: Optional[str] = None

class KPIMetrics(BaseModel):
    active_inpatient_roster: int = 128
    new_admissions_today: int = 3
    new_lab_ingestions: int = 7
    pending_doctor_signoff: int = 5
    flagged_inconsistencies: int = 2
    extraction_confidence_avg: float = 98.4

class LabResult(BaseModel):
    id: str
    test_code: str
    test_name: str
    result_value: str
    numeric_value: Optional[float] = None
    reference_interval: str
    unit: str
    status: str  # LOW, NORMAL, HIGH, CRITICAL
    source_report: str
    confidence: float
    verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None

class ConflictAlert(BaseModel):
    id: str
    conflict_type: str  # "ALLERGEN_MEDICATION", "DOSAGE_ANOMALY"
    severity: str       # "CRITICAL", "WARNING"
    current_statement: str
    historical_statement: str
    current_source: str
    historical_source: str
    recommendation: str
    safety_hold_active: bool = True
    resolved: bool = False

class TriagePatient(BaseModel):
    mrn: str
    name: str
    initials: str
    age: int
    gender: str
    room_bay: str
    admission_date: str
    urgency_tier: str   # "ACUTE_2H", "PRIORITY_24H", "ROUTINE_72H"
    summary: str
    labs: List[LabResult] = []
    conflicts: List[ConflictAlert] = []
    ready_for_review: bool = False
    doctor_note_drafted: bool = False

class PipelineStatus(BaseModel):
    stream_id: str = "#OCR-9920"
    file_name: str = "Metabolic_Panel_Vance.pdf"
    parsed_percentage: int = 98
    table_detection_status: str = "Ready for Physician Review"
    is_active: bool = True
    last_sync_time: str = "10:42 AM (St. Jude Epic)"

class FilterCounts(BaseModel):
    all: int = 3
    out_of_range: int = 1
    conflicts: int = 1
    pending_signoff: int = 1

class DashboardOverviewResponse(BaseModel):
    clinician: ClinicianProfile
    metrics: KPIMetrics
    pipeline: PipelineStatus
    filter_counts: FilterCounts = Field(default_factory=FilterCounts)

class VerifyLabRequest(BaseModel):
    notes: Optional[str] = None

class VerifyLabResponse(BaseModel):
    success: bool
    message: str
    lab: LabResult
    updated_pending_count: int

class ResolveConflictRequest(BaseModel):
    action: str  # "ENFORCE_BEDSIDE_HOLD", "OVERRIDE_CLINICAL"
    notes: Optional[str] = None

class BatchSignOffResponse(BaseModel):
    success: bool
    count_verified: int
    message: str
    remaining_pending: int

class EHRSyncResponse(BaseModel):
    success: bool
    sync_time: str
    patients_synced: int
    labs_updated: int
    message: str

class FlagNurseRequest(BaseModel):
    nurse_name: Optional[str] = "Nurse Kelly, RN"
    reason: Optional[str] = "Bedside allergy re-check & scratch test protocol"
    priority: Optional[str] = "URGENT"

class FlagNurseResponse(BaseModel):
    success: bool
    flag_id: str
    patient_mrn: str
    patient_name: str
    room_bay: str
    nurse_name: str
    reason: str
    priority: str
    status: str
    message: str
    timestamp: str

class LabOverrideRequest(BaseModel):
    result_value: str
    unit: Optional[str] = None
    reference_interval: Optional[str] = None
    status: Optional[str] = None
    override_reason: Optional[str] = None

class LabOverrideResponse(BaseModel):
    success: bool
    message: str
    updated_lab: dict

