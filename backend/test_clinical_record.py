import sys
import os

# Set python path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.database import DB_PATH

print("Testing MedLens Structured Clinical Record Backend API...")
print(f"Database Path: {DB_PATH}")

client = TestClient(app)

def test_clinical_record_endpoints():
    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] 1. Health check OK")

    # 2. GET full patient record for Arthur Pendleton (ML-9420)
    res = client.get("/api/records/patient/ML-9420")
    assert res.status_code == 200, f"GET patient failed: {res.text}"
    record = res.json()
    assert record["mrn"] == "ML-9420", f"Expected ML-9420, got {record['mrn']}"
    assert record["name"] == "Arthur Pendleton"
    assert len(record["biomarkers"]) == 5, f"Expected 5 biomarkers, got {len(record['biomarkers'])}"
    assert len(record["medications"]) == 4, f"Expected 4 medications, got {len(record['medications'])}"
    assert record["conflict"] is not None, "Expected active conflict"
    print(f"[PASS] 2. GET /api/records/patient/ML-9420 (Loaded {len(record['biomarkers'])} biomarkers, {len(record['medications'])} medications)")

    # 3. GET biomarkers directly and verify Zero-Hallucination policy
    res = client.get("/api/records/patient/ML-9420/biomarkers")
    assert res.status_code == 200
    biomarkers = res.json()
    # Check Creatinine status
    creatinine = next((b for b in biomarkers if "Creatinine" in b["analyte_name"]), None)
    assert creatinine is not None, "Creatinine observation not found"
    assert creatinine["reference_interval"] == "NOT DETERMINED FROM SOURCE"
    assert creatinine["status_flag"] == "NOT_DETERMINED"
    print(f"[PASS] 3. Zero-Hallucination Reference Range Verified (Creatinine ref: '{creatinine['reference_interval']}')")

    # 4. Verify a biomarker (LOINC 718-7 Hemoglobin)
    res = client.post("/api/records/verify-biomarker/ML-9420/718-7?clinician=Dr.%20Sarah%20Jenkins,%20MD")
    assert res.status_code == 200, f"Verify biomarker failed: {res.text}"
    verify_data = res.json()
    assert verify_data["success"] is True
    assert verify_data["biomarker"]["verified"] is True
    print(f"[PASS] 4. POST /api/records/verify-biomarker (Hemoglobin verified by {verify_data['biomarker']['verified_by']})")

    # 5. Resolve allergy conflict
    res = client.post("/api/records/resolve-allergy-conflict/ML-9420?clinician=Dr.%20Sarah%20Jenkins,%20MD")
    assert res.status_code == 200, f"Resolve allergy failed: {res.text}"
    allergy_data = res.json()
    assert allergy_data["success"] is True
    assert allergy_data["safety_hold_cleared"] is True
    print(f"[PASS] 5. POST /api/records/resolve-allergy-conflict (Allergy updated: {allergy_data['allergy_updated']})")

    # 6. Copilot Query (General and Allergy specific)
    res = client.post("/api/records/copilot/query", json={"patient_mrn": "ML-9420", "query": "What are the active antibiotic contraindications?"})
    assert res.status_code == 200
    copilot_data = res.json()
    assert "Critical Drug Conflict" in copilot_data["answer"] or "Penicillin" in copilot_data["answer"] or "Ampicillin" in copilot_data["answer"]
    assert len(copilot_data["citations"]) > 0
    print(f"[PASS] 6. POST /api/records/copilot/query (Grounded synthesis with {len(copilot_data['citations'])} citations returned)")

    # 7. Evidence OCR Layer
    res = client.get("/api/records/patient/ML-9420/evidence-ocr")
    assert res.status_code == 200
    evidence = res.json()
    assert evidence["document_id"] == "#LC-9941-A"
    assert len(evidence["lines"]) > 0
    print(f"[PASS] 7. GET /api/records/patient/ML-9420/evidence-ocr (Loaded {len(evidence['lines'])} OCR lines, match confidence {evidence['match_confidence']}%)")

    # 8. Cryptographic Physician Sign-Off
    res = client.post("/api/records/sign-off/ML-9420?clinician=Dr.%20Sarah%20Jenkins,%20MD", json={"notes": "Reviewed labs, adjusted Lasix, allergy hold logged."})
    assert res.status_code == 200
    signoff_data = res.json()
    assert signoff_data["success"] is True
    assert signoff_data["cryptographic_digest"].startswith("SHA256:")
    print(f"[PASS] 8. POST /api/records/sign-off/ML-9420 (Cryptographic Digest: {signoff_data['cryptographic_digest']})")

    print("\nALL 8 STRUCTURED CLINICAL RECORD TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_clinical_record_endpoints()
