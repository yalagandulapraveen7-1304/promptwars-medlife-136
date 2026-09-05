from typing import List, Optional
from enum import Enum
from pydantic import BaseModel

class DataProvenanceOrigin(str, Enum):
    PATIENT_PROVIDED = "PATIENT PROVIDED"
    EXTRACTED_FROM_REPORT = "EXTRACTED FROM REPORT"
    AI_GENERATED = "AI GENERATED"

class BiomarkerObservation(BaseModel):
    id: str
    patient_mrn: str
    loinc_code: str
    analyte_name: str
    methodology: str
    result_value: str
    numeric_value: Optional[float] = None
    unit: str
    reference_interval: str  # e.g. "12.0 – 16.0 g/dL" or "NOT DETERMINED FROM SOURCE"
    status_flag: str         # "LOW", "NORMAL", "HIGH", "CRITICAL", "NOT_DETERMINED"
    historical_previous: Optional[str] = None
    historical_delta: Optional[str] = None
    source_doc_id: str
    source_line: str         # e.g. "Line 14"
    confidence: float
    verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    provenance_origin: DataProvenanceOrigin = DataProvenanceOrigin.EXTRACTED_FROM_REPORT
    document_source: str = "LabCorp CBC Report #LC-9941-A"
    page_number: int = 1
    extracted_value: Optional[str] = None

class ActiveMedication(BaseModel):
    id: str
    patient_mrn: str
    medication_name: str
    dosage: str
    frequency: str
    route: str
    adherence_status: str    # "ACTIVE_COMPLIANT", "DISCONTINUED", "HOLD_REQUIRED"
    prescriber: str
    warning_flag: Optional[str] = None
    provenance_origin: DataProvenanceOrigin = DataProvenanceOrigin.EXTRACTED_FROM_REPORT
    document_source: Optional[str] = "Mercy General Discharge Summary #MG-4011"
    page_number: Optional[int] = 3

class ClinicalPresentation(BaseModel):
    patient_mrn: str
    chief_complaint: str
    functional_class: str    # "NYHA Class III"
    observations: str
    intake_nurse: str
    intake_timestamp: str
    provenance_origin: DataProvenanceOrigin = DataProvenanceOrigin.PATIENT_PROVIDED
    intake_source: str = "Bedside Electronic Intake Questionnaire (Self-Report)"

class EvidenceLine(BaseModel):
    line_number: int
    text_content: str
    is_highlighted: bool = False
    flag_label: Optional[str] = None
    biomarker_code: Optional[str] = None

class EvidenceLayer(BaseModel):
    document_title: str
    document_id: str
    specimen_date: str
    patient_mrn: str
    patient_name: str
    match_confidence: float
    lines: List[EvidenceLine]

class ConflictItem(BaseModel):
    id: str
    patient_mrn: str
    title: str
    severity: str            # "CRITICAL", "WARNING"
    current_statement: str
    historical_statement: str
    current_source: str
    historical_source: str
    recommendation: str
    safety_hold_active: bool
    resolved: bool
    current_source_origin: DataProvenanceOrigin = DataProvenanceOrigin.PATIENT_PROVIDED
    historical_source_origin: DataProvenanceOrigin = DataProvenanceOrigin.EXTRACTED_FROM_REPORT
    historical_page_number: int = 3

class AuditEntry(BaseModel):
    timestamp: str
    title: str
    performed_by: str
    details: str

class FullPatientRecord(BaseModel):
    mrn: str
    name: str
    initials: str
    age: int
    gender: str
    dob: str
    room_inpatient: str
    attending_physician: str
    inpatient_day: int
    cohort: str
    blood_group: str
    bmi: float
    payer: str
    ehr_synced: bool
    full_code: bool
    presentation: ClinicalPresentation
    biomarkers: List[BiomarkerObservation]
    medications: List[ActiveMedication]
    conflict: Optional[ConflictItem] = None
    audit_history: List[AuditEntry] = []
    is_signed_off: bool = False
    signed_off_at: Optional[str] = None
    signed_off_by: Optional[str] = None

class VerifyBiomarkerResponse(BaseModel):
    success: bool
    message: str
    biomarker: BiomarkerObservation

class ResolveAllergyConflictResponse(BaseModel):
    success: bool
    message: str
    safety_hold_cleared: bool
    allergy_updated: str

class CopilotQueryRequest(BaseModel):
    patient_mrn: str = "ML-9420"
    query: str

class CopilotQueryResponse(BaseModel):
    patient_mrn: str
    query: str
    answer: str
    citations: List[str]
    warnings: List[str] = []
    confidence_score: float = 98.8
    provenance_origin: DataProvenanceOrigin = DataProvenanceOrigin.AI_GENERATED
    ground_truth_isolation: bool = True

class PhysicianSignOffRequest(BaseModel):
    notes: Optional[str] = None

class PhysicianSignOffResponse(BaseModel):
    success: bool
    patient_mrn: str
    physician: str
    timestamp: str
    cryptographic_digest: str
    message: str
