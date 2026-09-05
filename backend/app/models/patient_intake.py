from typing import List, Optional
from pydantic import BaseModel, Field

class DemographicsInfo(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    preferred_name: Optional[str] = None
    dob: str
    age: Optional[int] = None
    legal_sex: str
    pronouns: Optional[str] = "she"
    mrn: str
    ssn_masked: Optional[str] = "***-**-4912"
    primary_language: str = "en"
    interpreter_required: bool = False

class ContactInfo(BaseModel):
    phone: Optional[str] = "+1 (555) 234-8910"
    email: Optional[str] = "eleanor.vance@example.org"
    street_address: Optional[str] = "742 Evergreen Terrace, Apt 4B"
    city: Optional[str] = "Springfield"
    state: Optional[str] = "IL"
    zip_code: Optional[str] = "62704"
    emergency_name: Optional[str] = "Thomas Vance"
    emergency_relation: Optional[str] = "Spouse"
    emergency_phone: Optional[str] = "+1 (555) 234-8911"

class InsuranceInfo(BaseModel):
    payer_name: str = "BlueCross BlueShield Comprehensive PPO"
    policy_id: str = "BCBS-IL-981240"
    group_num: str = "GRP-44102"
    subscriber_id: str = "SUB-881924"
    copay_tier: Optional[str] = "Tier 1 In-Network ($20 Specialist)"

class ClinicalTriageIntake(BaseModel):
    chief_complaint: str
    admission_date: str
    urgency_tier: str = "ACUTE_2H"  # "ACUTE_2H", "PRIORITY_24H", "ROUTINE_72H"
    assigned_ward: str = "Cardiology Unit 4B"
    assigned_room: str = "Room 412-B"
    attending_clinician: str = "Dr. Sarah Jenkins, MD"

class PatientIntakeSubmission(BaseModel):
    session_id: str = "#ENC-2026-8812"
    demographics: DemographicsInfo
    contact: ContactInfo = Field(default_factory=ContactInfo)
    insurance: InsuranceInfo = Field(default_factory=InsuranceInfo)
    clinical_triage: ClinicalTriageIntake
    symptoms: Optional[str] = None
    existing_conditions: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    other_notes: Optional[str] = None
    is_draft: bool = False

class PatientIntakeResponse(BaseModel):
    success: bool
    mrn: str
    session_id: str
    status: str  # "SUBMITTED", "DRAFT"
    message: str
    triage_enqueued: bool = True
    admitted_at: str

class NominationRequest(BaseModel):
    patient_mrn: str
    clinical_pathways: List[str] = ["Complex Heart Failure Cohort", "Cardiorenal Metabolic Review"]
    urgency_tier: str = "ACUTE_2H"
    attached_document_count: int = 3
    referring_doctor_notes: Optional[str] = "Admitted for acute exertional dyspnea and lower extremity edema."
    attending_doctor_signoff: bool = True
    signoff_doctor: str = "Dr. Sarah Jenkins, MD"

class NominationResponse(BaseModel):
    success: bool
    nomination_id: int
    patient_mrn: str
    status: str  # "PROCESSING", "QUEUED"
    readiness_score: int = 94
    message: str
    timestamp: str

class IntakePreFillBundle(BaseModel):
    source: str  # "wristband" or "epic"
    session_id: str
    demographics: DemographicsInfo
    contact: ContactInfo
    insurance: InsuranceInfo
    clinical_triage: ClinicalTriageIntake
    mpi_matched: bool = True
    confidence_score: float = 99.1
