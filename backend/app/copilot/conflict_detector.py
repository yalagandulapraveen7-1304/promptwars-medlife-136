from typing import List, Dict, Any, Optional
from app.models.copilot import CopilotConflictDetail

class ConflictDetector:
    """
    Cross-document discrepancy scanner enforcing MedLens Rule 3:
    Mandatory conflict detection with human verification flag (requires_human_verification).
    Never silently chooses or imputes one conflicting document value over another.
    """

    def __init__(self, conflicts_by_patient: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        self.conflicts_by_patient = conflicts_by_patient or {}

    def detect_conflicts(self, patient_id: str, patient_record: Optional[Dict[str, Any]] = None) -> List[CopilotConflictDetail]:
        """
        Scans for documented conflicts for a patient across intake, historical records, and EHR.
        """
        results: List[CopilotConflictDetail] = []

        # 1. Indexed controlled conflicts from dataset
        known_conflicts = self.conflicts_by_patient.get(patient_id, [])
        for c in known_conflicts:
            results.append(CopilotConflictDetail(
                conflict_id=c.get("conflict_id", f"CON-{patient_id}"),
                field=c.get("field", "allergies"),
                source_a=c.get("source_a", {}),
                source_b=c.get("source_b", {}),
                conflict_detected=c.get("conflict_detected", True),
                resolution=c.get("resolution", "requires_human_verification"),
                model_instruction=c.get("model_instruction", "Flag the conflict; never silently choose one value.")
            ))

        # 2. Dynamic heuristic inspection if not already in indexed set
        if not results and patient_record:
            allergies = patient_record.get("allergies", [])
            for al in allergies:
                if isinstance(al, dict) and al.get("status") in ["critical_conflict", "unverified"]:
                    # Found an allergy discrepancy
                    results.append(CopilotConflictDetail(
                        conflict_id=f"DYN-CON-{patient_id}",
                        field="allergies",
                        source_a={"document": "patient_intake", "value": "Unverified or self-reported intake"},
                        source_b={"document": "historical_record", "value": f"{al.get('allergen')} ({al.get('reaction', 'Severe reaction')})"},
                        conflict_detected=True,
                        resolution="requires_human_verification",
                        model_instruction="Allergy conflict identified; physician reconciliation required before prescribing."
                    ))

        return results

def detect_conflicts_for_patient(patient_id: str, conflicts_by_patient: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> List[CopilotConflictDetail]:
    detector = ConflictDetector(conflicts_by_patient)
    return detector.detect_conflicts(patient_id)
