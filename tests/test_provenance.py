import unittest
import sys
import os

backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.models.clinical_record import (
    DataProvenanceOrigin,
    BiomarkerObservation,
    ClinicalPresentation,
    CopilotQueryResponse
)
from app.database import get_patient_full_record, query_copilot_synthesis


class TestDataProvenance(unittest.TestCase):
    def test_provenance_enum_values(self):
        self.assertEqual(DataProvenanceOrigin.PATIENT_PROVIDED.value, "PATIENT PROVIDED")
        self.assertEqual(DataProvenanceOrigin.EXTRACTED_FROM_REPORT.value, "EXTRACTED FROM REPORT")
        self.assertEqual(DataProvenanceOrigin.AI_GENERATED.value, "AI GENERATED")

    def test_biomarker_provenance_extracted_from_report(self):
        bm = BiomarkerObservation(
            id="BM-1",
            patient_mrn="ML-9420",
            loinc_code="718-7",
            analyte_name="Hemoglobin (Hb)",
            methodology="Automated Spectrophotometry",
            result_value="10.2 g/dL",
            unit="g/dL",
            reference_interval="12.0 - 16.0 g/dL",
            status_flag="LOW",
            source_doc_id="#LC-9941-A",
            source_line="Line 14",
            confidence=99.4,
            provenance_origin=DataProvenanceOrigin.EXTRACTED_FROM_REPORT,
            document_source="LabCorp CBC Report #LC-9941-A",
            page_number=1,
            extracted_value="10.2 g/dL"
        )
        self.assertEqual(bm.provenance_origin, DataProvenanceOrigin.EXTRACTED_FROM_REPORT)
        self.assertEqual(bm.document_source, "LabCorp CBC Report #LC-9941-A")
        self.assertEqual(bm.page_number, 1)
        self.assertEqual(bm.extracted_value, "10.2 g/dL")
        self.assertEqual(bm.reference_interval, "12.0 - 16.0 g/dL")

    def test_presentation_provenance_patient_provided(self):
        cp = ClinicalPresentation(
            patient_mrn="ML-9420",
            chief_complaint="Severe exertional dyspnea",
            functional_class="NYHA Class III",
            observations="Stable baseline",
            intake_nurse="Nurse Kelly, RN",
            intake_timestamp="14 Oct 2026, 08:30 AM EDT",
            provenance_origin=DataProvenanceOrigin.PATIENT_PROVIDED,
            intake_source="Bedside Electronic Intake Questionnaire (Self-Report)"
        )
        self.assertEqual(cp.provenance_origin, DataProvenanceOrigin.PATIENT_PROVIDED)

    def test_copilot_provenance_ai_generated_isolation(self):
        cq = CopilotQueryResponse(
            patient_mrn="ML-9420",
            query="Summarize findings",
            answer="Patient has microcytic anemia.",
            citations=["LabCorp Report #LC-9941-A, Page 1, Line 14"],
            provenance_origin=DataProvenanceOrigin.AI_GENERATED,
            ground_truth_isolation=True
        )
        self.assertEqual(cq.provenance_origin, DataProvenanceOrigin.AI_GENERATED)
        self.assertTrue(cq.ground_truth_isolation)

    def test_database_record_provenance_enrichment(self):
        record = get_patient_full_record("ML-9420")
        self.assertIsNotNone(record)
        self.assertEqual(record["presentation"]["provenance_origin"], "PATIENT PROVIDED")
        self.assertTrue(len(record["biomarkers"]) > 0)
        for bm in record["biomarkers"]:
            self.assertEqual(bm["provenance_origin"], "EXTRACTED FROM REPORT")
            self.assertIn("page_number", bm)
            self.assertIn("document_source", bm)
        self.assertEqual(record["conflict"]["current_source_origin"], "PATIENT PROVIDED")
        self.assertEqual(record["conflict"]["historical_source_origin"], "EXTRACTED FROM REPORT")

    def test_copilot_synthesis_provenance(self):
        res = query_copilot_synthesis("ML-9420", "Summarize lab results")
        self.assertEqual(res["provenance_origin"], "AI GENERATED")
        self.assertTrue(res["ground_truth_isolation"])


if __name__ == "__main__":
    unittest.main()
