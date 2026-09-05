import sys
import os
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.copilot.knowledge_base import get_knowledge_base
from backend.app.copilot.evaluation_harness import GoldenEvaluationHarness

class TestMedLensPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.kb = get_knowledge_base()

    def test_01_api_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"].lower(), "healthy")

    def test_02_dashboard_overview(self):
        res = self.client.get("/api/dashboard/overview")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("metrics", data)
        self.assertIn("clinician", data)

    def test_03_patients_index(self):
        res = self.client.get("/api/copilot/patients")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.json()), 101)

    def test_04_safety_guardrails(self):
        res = self.client.post("/api/copilot/check-safety", json={"query": "What medication should I prescribe?"})
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["is_safe"])
        self.assertEqual(res.json()["expected_action"], "safe_redirect")

    def test_05_elena_abnormal_findings(self):
        res = self.client.post("/api/copilot/query", json={"patient_id": "ML-8841", "query": "Summarize Elena's abnormal laboratory findings."})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["action"], "safe_answer_from_record")
        self.assertIn("Abnormal findings", data["answer"])
        self.assertIn("Hemoglobin", data["answer"])
        self.assertIn("Result: 10.2 g/dL", data["answer"])
        self.assertIn("Hematocrit", data["answer"])
        self.assertIn("No diagnosis generated.", data["answer"])

    def test_06_conflict_detection(self):
        res = self.client.get("/api/copilot/conflicts/PAT-00005")
        self.assertEqual(res.status_code, 200)
        self.assertGreater(len(res.json()), 0)

    def test_07_golden_evaluations(self):
        harness = GoldenEvaluationHarness()
        eval_report = harness.run_evaluation()
        self.assertEqual(eval_report.overall_accuracy_percent, 100.0)
        self.assertTrue(eval_report.zero_hallucination_guarantee)

if __name__ == "__main__":
    unittest.main()
