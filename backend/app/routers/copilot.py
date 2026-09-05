from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.copilot import (
    CopilotQueryRequest,
    CopilotQueryResponse,
    SafetyCheckRequest,
    SafetyCheckResponse,
    PatientSummaryItem,
    CopilotEvaluationReport,
    CopilotConflictDetail
)
from app.copilot.knowledge_base import get_knowledge_base
from app.copilot.engine import get_copilot_engine
from app.copilot.safety_guardrails import check_safety
from app.copilot.conflict_detector import detect_conflicts_for_patient
from app.copilot.evaluation_harness import GoldenEvaluationHarness

router = APIRouter(prefix="/api/copilot", tags=["MedLens AI Copilot"])

@router.post("/query", response_model=CopilotQueryResponse)
def execute_copilot_query(req: CopilotQueryRequest):
    """
    Main Copilot reasoning endpoint.
    Performs safety screening, cross-document conflict checks, biomarker analysis,
    and source-grounded clinical synthesis with line-level citations.
    """
    engine = get_copilot_engine()
    return engine.query(patient_id=req.patient_id, query_text=req.query)

@router.get("/patients", response_model=List[PatientSummaryItem])
def get_copilot_patients():
    """
    Lists all indexed patients available to Copilot (100 synthetic + Arthur Pendleton ML-9420).
    """
    kb = get_knowledge_base()
    results = []
    for pid, p in kb.patients.items():
        reps = kb.get_patient_reports(pid)
        conflicts = kb.get_patient_conflicts(pid)
        results.append(PatientSummaryItem(
            patient_id=pid,
            name=p.get("name", "Unknown"),
            age=p.get("age", 0),
            sex=p.get("sex", "Unknown"),
            symptoms=p.get("symptoms", []),
            conditions=p.get("existing_conditions", []),
            has_conflicts=len(conflicts) > 0,
            report_count=len(reps)
        ))
    return results

@router.get("/patient/{patient_id}/context")
def get_patient_copilot_context(patient_id: str):
    """
    Fetches full clinical context for a patient including demographics,
    laboratory reports, structured lab results, prescriptions, clinical notes, and conflicts.
    """
    kb = get_knowledge_base()
    patient = kb.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found in index.")
    
    return {
        "patient": patient,
        "reports": kb.get_patient_reports(patient_id),
        "lab_results": kb.get_lab_results(patient_id),
        "prescriptions": kb.prescriptions_by_patient.get(patient_id, []),
        "clinical_notes": kb.clinical_notes_by_patient.get(patient_id, []),
        "conflicts": kb.get_patient_conflicts(patient_id),
        "missing_info": kb.get_patient_missing_info(patient_id),
        "comparisons": kb.get_patient_comparisons(patient_id),
        "provenance": kb.get_patient_provenance(patient_id)
    }

@router.post("/check-safety", response_model=SafetyCheckResponse)
def evaluate_prompt_safety(body: SafetyCheckRequest):
    """
    Dedicated endpoint to test a query against the 15 MedLens Safety Rules.
    Verifies that autonomous diagnosis, prescribing, or dosing requests trigger safe_redirect.
    """
    kb = get_knowledge_base()
    return check_safety(body.query, safety_examples=kb.safety_examples)

@router.get("/conflicts/{patient_id}", response_model=List[CopilotConflictDetail])
def get_patient_conflicts_endpoint(patient_id: str):
    """
    Returns detected cross-document conflicts requiring mandatory human verification.
    """
    kb = get_knowledge_base()
    return detect_conflicts_for_patient(patient_id, kb.conflicts_by_patient)

@router.get("/evaluate", response_model=CopilotEvaluationReport)
def run_evaluation_benchmark(limit: Optional[int] = Query(None, description="Optional patient count limit")):
    """
    Executes automated evaluation across the 100-patient golden benchmark in evaluation/golden_evaluation.json.
    Verifies 100% zero-hallucination compliance and safety redirect adherence.
    """
    harness = GoldenEvaluationHarness()
    return harness.run_evaluation(limit=limit)
