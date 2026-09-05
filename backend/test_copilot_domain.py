import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_domain():
    # 1. Non-Medical Queries
    non_med = [
        "What is the capital of France?",
        "Who won the football World Cup?",
        "Recipe for chocolate cake",
        "Write python code to sort a list",
        "Tell me a funny joke",
        "How to repair a flat car tire?",
        "What is the price of bitcoin?"
    ]
    for q in non_med:
        res = client.post("/api/copilot/query", json={"patient_id": "ML-8841", "query": q})
        assert res.status_code == 200, f"Query failed for {q}: {res.text}"
        d = res.json()
        assert d["action"] == "out_of_domain", f"Expected out_of_domain for '{q}', got {d['action']}"
        assert "valid medical" in d["answer"].lower() or "guardrail" in d["answer"].lower()
        print(f"[PASS] Non-medical intercepted: '{q}' -> action='{d['action']}' with valid input examples.")

    # 2. Medical queries
    medical = [
        "Summarize out-of-range lab results for Elena Rostova",
        "What is the reference range for Hemoglobin?",
        "Check penicillin allergy conflict for Marcus Vance",
        "Compare consecutive reports for this patient"
    ]
    for q in medical:
        res = client.post("/api/copilot/query", json={"patient_id": "ML-8841", "query": q})
        assert res.status_code == 200
        d = res.json()
        assert d["action"] in ["safe_answer_from_record", "show_provenance"], f"Expected in-domain for '{q}', got {d['action']}"
        print(f"[PASS] Medical query accepted: '{q}' -> action='{d['action']}'")

    print("\n================================================================================")
    print("ALL COPILOT DOMAIN SCOPE & MEDICAL INPUT GUIDANCE TESTS PASSED!")
    print("================================================================================")

if __name__ == "__main__":
    test_domain()
