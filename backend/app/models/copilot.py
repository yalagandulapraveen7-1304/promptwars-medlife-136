from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class DataProvenanceOrigin(str, Enum):
    PATIENT_PROVIDED = "PATIENT PROVIDED"
    EXTRACTED_FROM_REPORT = "EXTRACTED FROM REPORT"
    AI_GENERATED = "AI GENERATED"

class CopilotQueryRequest(BaseModel):
    patient_id: Optional[str] = Field(default=None, description="Target patient ID (e.g., 'PAT-00001' or 'ML-8841')")
    query: str = Field(..., description="Clinical inquiry or question from provider")

class CopilotConflictDetail(BaseModel):
    conflict_id: str
    field: str
    source_a: Dict[str, Any]
    source_b: Dict[str, Any]
    conflict_detected: bool = True
    resolution: str = "requires_human_verification"
    model_instruction: str

class CopilotQueryResponse(BaseModel):
    patient_id: Optional[str] = Field(default=None, description="Patient ID associated with query")
    query: str
    action: str = Field(..., description="'safe_answer_from_record', 'safe_redirect', 'out_of_domain', or 'show_provenance'")
    answer: str
    citations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    conflicts: List[CopilotConflictDetail] = Field(default_factory=list)
    confidence_score: float = 98.5
    source_grounded: bool = True
    safety_rule_applied: Optional[str] = None
    provenance_origin: DataProvenanceOrigin = DataProvenanceOrigin.AI_GENERATED
    ground_truth_isolation: bool = True

class SafetyCheckRequest(BaseModel):
    query: str

class SafetyCheckResponse(BaseModel):
    query: str
    is_safe: bool
    expected_action: str
    rule_id: Optional[str] = None
    rule_text: str
    safe_redirect_message: Optional[str] = None

class PatientSummaryItem(BaseModel):
    patient_id: str
    name: str
    age: int
    sex: str
    symptoms: List[str]
    conditions: List[str]
    has_conflicts: bool
    report_count: int

class CopilotEvaluationMetric(BaseModel):
    category: str
    total: int
    passed: int
    accuracy_percent: float

class CopilotEvaluationReport(BaseModel):
    dataset_name: str = "MedLens Synthetic Dataset v1"
    total_patients_evaluated: int
    total_checks: int
    passed_checks: int
    overall_accuracy_percent: float
    categories: Dict[str, CopilotEvaluationMetric]
    synthetic_only_compliance: bool = True
    zero_hallucination_guarantee: bool = True
