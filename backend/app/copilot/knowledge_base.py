import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("medlens.copilot.kb")

DEFAULT_DATASET_DIR = r"C:\Users\ammul\Downloads\medlens_synthetic_dataset_v1"

class KnowledgeBase:
    """
    Central repository indexer for MedLens Synthetic Dataset v1.
    Loads and provides indexed, in-memory lookups for 100 synthetic patients,
    300 laboratory reports, 2,400 lab result records, 400 QA pairs, 20 conflicts,
    provenance, and the golden evaluation benchmark.
    """
    _instance: Optional["KnowledgeBase"] = None

    def __init__(self, dataset_dir: Optional[str] = None):
        self.dataset_dir = dataset_dir or os.environ.get("MEDLENS_DATASET_DIR", DEFAULT_DATASET_DIR)
        self.patients: Dict[str, Dict[str, Any]] = {}
        self.reports_by_patient: Dict[str, List[Dict[str, Any]]] = {}
        self.reports_by_id: Dict[str, Dict[str, Any]] = {}
        self.lab_results_by_patient: Dict[str, List[Dict[str, Any]]] = {}
        self.lab_results_by_report: Dict[str, List[Dict[str, Any]]] = {}
        self.prescriptions_by_patient: Dict[str, List[Dict[str, Any]]] = {}
        self.clinical_notes_by_patient: Dict[str, List[Dict[str, Any]]] = {}
        self.doctor_qa_list: List[Dict[str, Any]] = []
        self.qa_by_patient: Dict[str, List[Dict[str, Any]]] = {}
        self.missing_info_by_patient: Dict[str, Dict[str, Any]] = {}
        self.comparisons_by_patient: Dict[str, List[Dict[str, Any]]] = {}
        self.conflicts_by_patient: Dict[str, List[Dict[str, Any]]] = {}
        self.provenance_by_patient: Dict[str, List[Dict[str, Any]]] = {}
        self.safety_examples: List[Dict[str, Any]] = []
        self.golden_evaluations: List[Dict[str, Any]] = []
        
        self.load_all()

    def _read_json(self, *rel_path) -> Any:
        path = os.path.join(self.dataset_dir, *rel_path)
        if not os.path.exists(path):
            logger.warning(f"File not found: {path}")
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON from {path}: {e}")
            return []

    def _read_jsonl(self, *rel_path) -> List[Dict[str, Any]]:
        path = os.path.join(self.dataset_dir, *rel_path)
        if not os.path.exists(path):
            logger.warning(f"File not found: {path}")
            return []
        results = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        results.append(json.loads(line))
        except Exception as e:
            logger.error(f"Error reading JSONL from {path}: {e}")
        return results

    def load_all(self):
        logger.info(f"Loading MedLens Synthetic Dataset from: {self.dataset_dir}")

        # 1. Patients
        pts = self._read_json("patients", "patients.json")
        for p in pts:
            pid = p.get("patient_id")
            if pid:
                self.patients[pid] = p

        # Integrate Arthur Pendleton (ML-9420) as a first-class patient in the Copilot index
        self.patients["ML-9420"] = {
            "patient_id": "ML-9420",
            "name": "Arthur Pendleton",
            "age": 67,
            "sex": "Male",
            "symptoms": ["Shortness of breath", "Orthopnea", "Bilateral lower extremity pitting edema", "NYHA Class III"],
            "existing_conditions": ["Congestive Heart Failure", "Coronary Artery Disease", "Type 2 Diabetes Mellitus"],
            "allergies": [
                {"allergen": "Penicillin / Ampicillin", "status": "critical_conflict", "reaction": "Cutaneous rash & hives", "source": "Mercy General 2022"}
            ],
            "medications": [
                {"name": "Furosemide (Lasix)", "dosage": "40mg oral daily", "status": "active"},
                {"name": "Lisinopril", "dosage": "20mg oral daily", "status": "active"},
                {"name": "Metoprolol Succinate", "dosage": "50mg oral daily", "status": "active"},
                {"name": "Ceftriaxone", "dosage": "1g IV scheduled", "status": "held_allergy_conflict"}
            ],
            "data_status": "gold_clinical_benchmark"
        }

        # 2. Reports
        reps = self._read_json("reports", "reports.json")
        for r in reps:
            pid = r.get("patient_id")
            rid = r.get("report_id")
            if pid:
                self.reports_by_patient.setdefault(pid, []).append(r)
            if rid:
                self.reports_by_id[rid] = r

        # Sort each patient's reports chronologically
        for pid, r_list in self.reports_by_patient.items():
            r_list.sort(key=lambda x: x.get("report_date", ""))

        # Arthur Pendleton Report
        arthur_rep = {
            "patient_id": "ML-9420",
            "report_id": "LC-9941-A",
            "report_date": "2026-10-14",
            "report_type": "laboratory",
            "raw_text": "LabCorp Inpatient CBC & Comprehensive Panel\nSpecimen #LC-9941-A\nHemoglobin: 10.2 g/dL (Ref: 12.0-16.0) [LOW]\nHematocrit: 31.4 % (Ref: 37.0-48.0) [LOW]\nPlatelets: 245 x10^3/uL (Ref: 150-450) [NORMAL]\nFerritin: 18 ng/mL (Ref: 24-336) [LOW]\nCreatinine: 1.4 mg/dL (Ref: NOT DETERMINED FROM SOURCE)",
            "synthetic": False
        }
        self.reports_by_patient.setdefault("ML-9420", []).append(arthur_rep)
        self.reports_by_id["LC-9941-A"] = arthur_rep

        # 3. Lab Results
        labs = self._read_json("reports", "lab_results.json")
        for lb in labs:
            pid = lb.get("patient_id")
            rid = lb.get("report_id")
            if pid:
                self.lab_results_by_patient.setdefault(pid, []).append(lb)
            if rid:
                self.lab_results_by_report.setdefault(rid, []).append(lb)

        # Arthur Pendleton Lab Results
        arthur_labs = [
            {"patient_id": "ML-9420", "report_id": "LC-9941-A", "report_date": "2026-10-14", "test_name": "Hemoglobin", "value": 10.2, "unit": "g/dL", "reference_low": 12.0, "reference_high": 16.0, "status": "low"},
            {"patient_id": "ML-9420", "report_id": "LC-9941-A", "report_date": "2026-10-14", "test_name": "Hematocrit", "value": 31.4, "unit": "%", "reference_low": 37.0, "reference_high": 48.0, "status": "low"},
            {"patient_id": "ML-9420", "report_id": "LC-9941-A", "report_date": "2026-10-14", "test_name": "Platelet Count", "value": 245000.0, "unit": "/µL", "reference_low": 150000.0, "reference_high": 450000.0, "status": "normal"},
            {"patient_id": "ML-9420", "report_id": "LC-9941-A", "report_date": "2026-10-14", "test_name": "Serum Ferritin", "value": 18.0, "unit": "ng/mL", "reference_low": 24.0, "reference_high": 336.0, "status": "low"},
            {"patient_id": "ML-9420", "report_id": "LC-9941-A", "report_date": "2026-10-14", "test_name": "Serum Creatinine", "value": 1.4, "unit": "mg/dL", "reference_low": None, "reference_high": None, "status": "unverified"}
        ]
        self.lab_results_by_patient["ML-9420"] = arthur_labs
        self.lab_results_by_report["LC-9941-A"] = arthur_labs

        # 4. Prescriptions
        r_rx = self._read_json("reports", "prescriptions.json")
        for rx in r_rx:
            pid = rx.get("patient_id")
            if pid:
                self.prescriptions_by_patient.setdefault(pid, []).append(rx)

        # 5. Clinical Notes
        notes = self._read_json("reports", "clinical_notes.json")
        for cn in notes:
            pid = cn.get("patient_id")
            if pid:
                self.clinical_notes_by_patient.setdefault(pid, []).append(cn)

        # 6. Doctor QA & Chatbot pairs
        qa_data = self._read_json("chatbot", "doctor_qa.json")
        if isinstance(qa_data, list):
            self.doctor_qa_list.extend(qa_data)
        
        train_qa = self._read_jsonl("chatbot", "train.jsonl")
        self.doctor_qa_list.extend(train_qa)

        for qa in self.doctor_qa_list:
            pid = qa.get("patient_id")
            if pid:
                self.qa_by_patient.setdefault(pid, []).append(qa)

        # 7. Missing Information Patterns
        mis_data = self._read_json("chatbot", "missing_information.json")
        for m in mis_data:
            pid = m.get("patient_id")
            if pid:
                self.missing_info_by_patient[pid] = m

        # 8. Report Comparisons
        cmp_data = self._read_json("chatbot", "report_comparison.json")
        for c in cmp_data:
            pid = c.get("patient_id")
            if pid:
                self.comparisons_by_patient.setdefault(pid, []).append(c)

        # 9. Controlled Conflicts
        conf_data = self._read_json("conflicts", "conflicts.json")
        for cf in conf_data:
            pid = cf.get("patient_id")
            if pid:
                self.conflicts_by_patient.setdefault(pid, []).append(cf)

        # Arthur Pendleton conflict
        self.conflicts_by_patient.setdefault("ML-9420", []).append({
            "conflict_id": "CON-ML-9420",
            "patient_id": "ML-9420",
            "field": "allergies",
            "source_a": {
                "document": "patient_intake",
                "value": "No Known Drug Allergies (self-reported)"
            },
            "source_b": {
                "document": "Mercy General 2022 Transfer Note, Page 3, Line 41",
                "value": "Penicillin & Ampicillin (Cutaneous rash & hives)"
            },
            "conflict_detected": True,
            "resolution": "requires_human_verification",
            "model_instruction": "Flag critical antibiotic safety conflict; never administer beta-lactam class without physician override."
        })

        # 10. Provenance
        prov_data = self._read_json("provenance", "provenance.json")
        for pr in prov_data:
            pid = pr.get("patient_id")
            if pid:
                self.provenance_by_patient.setdefault(pid, []).append(pr)

        # 11. Safety Examples
        self.safety_examples = self._read_json("safety", "safety_examples.json")

        # 12. Golden Evaluation Set
        self.golden_evaluations = self._read_json("evaluation", "golden_evaluation.json")

        logger.info(
            f"KnowledgeBase loaded: {len(self.patients)} patients, "
            f"{len(self.reports_by_id)} lab reports, {len(self.doctor_qa_list)} QA examples, "
            f"{sum(len(v) for v in self.conflicts_by_patient.values())} conflict cases."
        )

    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        return self.patients.get(patient_id)

    def get_patient_reports(self, patient_id: str) -> List[Dict[str, Any]]:
        return self.reports_by_patient.get(patient_id, [])

    def get_latest_report(self, patient_id: str) -> Optional[Dict[str, Any]]:
        reps = self.get_patient_reports(patient_id)
        return reps[-1] if reps else None

    def get_lab_results(self, patient_id: str, report_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if report_id:
            return self.lab_results_by_report.get(report_id, [])
        return self.lab_results_by_patient.get(patient_id, [])

    def get_patient_conflicts(self, patient_id: str) -> List[Dict[str, Any]]:
        return self.conflicts_by_patient.get(patient_id, [])

    def get_patient_provenance(self, patient_id: str) -> List[Dict[str, Any]]:
        return self.provenance_by_patient.get(patient_id, [])

    def get_patient_missing_info(self, patient_id: str) -> Optional[Dict[str, Any]]:
        return self.missing_info_by_patient.get(patient_id)

    def get_patient_comparisons(self, patient_id: str) -> List[Dict[str, Any]]:
        return self.comparisons_by_patient.get(patient_id, [])

_kb_instance: Optional[KnowledgeBase] = None

def get_knowledge_base() -> KnowledgeBase:
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
