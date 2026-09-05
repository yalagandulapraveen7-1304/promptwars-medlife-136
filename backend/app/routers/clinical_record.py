from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.clinical_record import (
    FullPatientRecord,
    BiomarkerObservation,
    EvidenceLayer,
    VerifyBiomarkerResponse,
    ResolveAllergyConflictResponse,
    CopilotQueryRequest,
    CopilotQueryResponse,
    PhysicianSignOffRequest,
    PhysicianSignOffResponse
)
from app.database import (
    get_patient_full_record,
    verify_biomarker,
    resolve_patient_allergy,
    sign_off_clinical_record,
    get_evidence_layer_data,
    query_copilot_synthesis
)

router = APIRouter(prefix="/api/records", tags=["Structured Clinical Record"])

@router.get("/patient/{patient_mrn}", response_model=FullPatientRecord)
def get_patient_record(patient_mrn: str):
    """
    Fetch comprehensive structured clinical record for a patient (Module 6 & 7).
    Includes clinical presentation, extracted biomarkers with provenance lines,
    medications, active safety conflicts, and audit trail.
    """
    record = get_patient_full_record(patient_mrn)
    if not record:
        raise HTTPException(status_code=404, detail=f"Patient record for MRN {patient_mrn} not found.")
    return record

@router.get("/patient/{patient_mrn}/biomarkers", response_model=List[BiomarkerObservation])
def get_patient_biomarkers(patient_mrn: str):
    """
    Fetch list of laboratory biomarkers with strict reference range awareness.
    Adheres to the zero-hallucination policy (e.g. Creatinine marked NOT DETERMINED FROM SOURCE).
    """
    record = get_patient_full_record(patient_mrn)
    if not record:
        raise HTTPException(status_code=404, detail=f"Patient record for MRN {patient_mrn} not found.")
    return record["biomarkers"]

@router.post("/verify-biomarker/{patient_mrn}/{biomarker_code}", response_model=VerifyBiomarkerResponse)
def verify_patient_biomarker(
    patient_mrn: str,
    biomarker_code: str,
    clinician: str = Query("Dr. Sarah Jenkins, MD", description="Attending physician confirming extraction")
):
    """
    Physician verification of an extracted biomarker observation.
    Sets verification timestamp, records clinician signature in the audit trail,
    and locks provenance.
    """
    updated_bm = verify_biomarker(patient_mrn, biomarker_code, clinician_name=clinician)
    if not updated_bm:
        raise HTTPException(status_code=404, detail=f"Biomarker {biomarker_code} not found for patient {patient_mrn}")
    
    return VerifyBiomarkerResponse(
        success=True,
        message=f"Biomarker {biomarker_code} successfully verified by {clinician}.",
        biomarker=updated_bm
    )

@router.post("/resolve-allergy-conflict/{patient_mrn}", response_model=ResolveAllergyConflictResponse)
def resolve_allergy_discrepancy(
    patient_mrn: str,
    clinician: str = Query("Dr. Sarah Jenkins, MD", description="Attending physician accepting resolution")
):
    """
    Resolves cross-document discrepancy between patient intake and historical EHR.
    Clears safety hold on antibiotic contraindications and logs reconciled allergy in EHR master registry.
    """
    success, allergy_updated = resolve_patient_allergy(patient_mrn, clinician_name=clinician)
    return ResolveAllergyConflictResponse(
        success=success,
        message=f"Discrepancy resolved. Allergy profile committed to EHR by {clinician}.",
        safety_hold_cleared=True,
        allergy_updated=allergy_updated
    )

@router.post("/copilot/query", response_model=CopilotQueryResponse)
def query_copilot(req: CopilotQueryRequest):
    """
    Grounded clinical copilot synthesis (Modules 12 & 14).
    Produces synthesized clinical recommendations with exact document & line citations
    and strict reference range disclosures.
    """
    result = query_copilot_synthesis(req.patient_mrn, req.query)
    return result

@router.post("/sign-off/{patient_mrn}", response_model=PhysicianSignOffResponse)
def sign_off_record(
    patient_mrn: str,
    body: PhysicianSignOffRequest,
    clinician: str = Query("Dr. Sarah Jenkins, MD", description="Attending signing off")
):
    """
    Master physician sign-off with cryptographic hash digest (Module 23).
    Attests full clinical review and seals structured record for EHR push.
    """
    digest, signed_at = sign_off_clinical_record(patient_mrn, clinician_name=clinician, notes=body.notes)
    return PhysicianSignOffResponse(
        success=True,
        patient_mrn=patient_mrn,
        physician=clinician,
        timestamp=signed_at,
        cryptographic_digest=digest,
        message=f"Master clinical record signed and sealed by {clinician}."
    )

@router.get("/patient/{patient_mrn}/evidence-ocr", response_model=EvidenceLayer)
def get_evidence_layer(patient_mrn: str):
    """
    Fetches the side-by-side evidence OCR bounding lines and extraction confidence (Modules 13 & 14).
    """
    return get_evidence_layer_data(patient_mrn)
