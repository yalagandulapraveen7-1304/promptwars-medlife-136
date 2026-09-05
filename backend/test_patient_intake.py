import sys
import os

# Set python path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.database import DB_PATH

print("Testing MedLens Patient Intake & Nomination Backend API...")
print(f"Database Path: {DB_PATH}")

client = TestClient(app)

def test_patient_intake_endpoints():
    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    print("[PASS] 1. Health check OK")

    # 2. GET prefill from wristband barcode scan
    res = client.get("/api/intake/prefill?source=wristband")
    assert res.status_code == 200, f"Prefill failed: {res.text}"
    wristband_data = res.json()
    assert wristband_data["source"] == "wristband"
    assert wristband_data["demographics"]["first_name"] == "Eleanor"
    assert wristband_data["demographics"]["mrn"] == "ML-9420-TX"
    assert wristband_data["mpi_matched"] is True
    print(f"[PASS] 2. GET /api/intake/prefill?source=wristband (Matched MPI: {wristband_data['demographics']['first_name']} {wristband_data['demographics']['last_name']})")

    # 3. GET prefill from Epic / Cerner EHR pull
    res = client.get("/api/intake/prefill?source=epic")
    assert res.status_code == 200
    epic_data = res.json()
    assert epic_data["source"] == "epic"
    assert "Orthopnea" in epic_data["clinical_triage"]["chief_complaint"] or "dyspnea" in epic_data["clinical_triage"]["chief_complaint"]
    print("[PASS] 3. GET /api/intake/prefill?source=epic (EHR FHIR pre-fill pulled successfully)")

    # 4. Save intake draft
    draft_payload = {
        "session_id": "#ENC-2026-8812",
        "demographics": {
            "first_name": "Eleanor",
            "middle_name": "Grace",
            "last_name": "Vance",
            "preferred_name": "Ellie",
            "dob": "1968-04-18",
            "age": 58,
            "legal_sex": "female",
            "pronouns": "she",
            "mrn": "ML-9420-TX",
            "ssn_masked": "***-**-4912",
            "primary_language": "en",
            "interpreter_required": False
        },
        "contact": {
            "phone": "+1 (555) 234-8910",
            "email": "eleanor.vance@example.org",
            "street_address": "742 Evergreen Terrace, Apt 4B",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62704",
            "emergency_name": "Thomas Vance",
            "emergency_relation": "Spouse",
            "emergency_phone": "+1 (555) 234-8911"
        },
        "insurance": {
            "payer_name": "BlueCross BlueShield Comprehensive PPO",
            "policy_id": "BCBS-IL-981240",
            "group_num": "GRP-44102",
            "subscriber_id": "SUB-881924",
            "copay_tier": "Tier 1 In-Network ($20 Specialist)"
        },
        "clinical_triage": {
            "chief_complaint": "Exertional dyspnea and bilateral leg swelling",
            "admission_date": "14 Oct 2026",
            "urgency_tier": "ACUTE_2H",
            "assigned_ward": "Cardiology Unit 4B",
            "assigned_room": "Room 412-B",
            "attending_clinician": "Dr. Sarah Jenkins, MD"
        },
        "is_draft": True
    }
    res = client.post("/api/intake/save-draft", json=draft_payload)
    assert res.status_code == 200, f"Save draft failed: {res.text}"
    save_draft_resp = res.json()
    assert save_draft_resp["status"] == "DRAFT"
    print("[PASS] 4. POST /api/intake/save-draft (Draft stored)")

    # 5. GET saved intake record
    res = client.get("/api/intake/ML-9420-TX")
    assert res.status_code == 200, f"Get intake failed: {res.text}"
    intake_record = res.json()
    assert intake_record["demographics"]["first_name"] == "Eleanor"
    assert intake_record["contact"]["city"] == "Springfield"
    print(f"[PASS] 5. GET /api/intake/ML-9420-TX (Retrieved intake record: {intake_record['demographics']['first_name']} {intake_record['demographics']['last_name']})")

    # 6. Submit finalized Patient Intake (Demographics through Clinical Triage)
    submit_payload = dict(draft_payload)
    submit_payload["is_draft"] = False
    res = client.post("/api/intake/submit", json=submit_payload)
    assert res.status_code == 200, f"Submit intake failed: {res.text}"
    submit_resp = res.json()
    assert submit_resp["status"] == "SUBMITTED"
    assert submit_resp["triage_enqueued"] is True
    print(f"[PASS] 6. POST /api/intake/submit (Patient {submit_resp['mrn']} enqueued for triage)")

    # 7. Verify newly submitted patient appears on Doctor Dashboard triage queue
    res = client.get("/api/dashboard/triage-queue?q=Vance")
    assert res.status_code == 200
    search_results = res.json()
    found = any("Eleanor" in p["name"] or "Vance" in p["name"] for p in search_results)
    assert found, "Submitted patient Eleanor Vance not found in dashboard triage queue"
    print(f"[PASS] 7. Dashboard Integration Verified: Eleanor Vance present in Doctor Triage queue")

    # 8. Submit Patient Nomination for processing
    nomination_payload = {
        "patient_mrn": "ML-9420-TX",
        "clinical_pathways": ["Complex Heart Failure Cohort", "Cardiorenal Metabolic Review"],
        "urgency_tier": "ACUTE_2H",
        "attached_document_count": 3,
        "referring_doctor_notes": "Admitted for decompensated heart failure with preserved EF.",
        "attending_doctor_signoff": True,
        "signoff_doctor": "Dr. Sarah Jenkins, MD"
    }
    res = client.post("/api/intake/nominate", json=nomination_payload)
    assert res.status_code == 200, f"Nominate failed: {res.text}"
    nom_resp = res.json()
    assert nom_resp["success"] is True
    assert nom_resp["readiness_score"] == 94
    print(f"[PASS] 8. POST /api/intake/nominate (Nomination #{nom_resp['nomination_id']} dispatched, Readiness Score: {nom_resp['readiness_score']}%)")

    # 9. GET Readiness Score
    res = client.get("/api/intake/readiness-score/ML-9420-TX")
    assert res.status_code == 200
    readiness_data = res.json()
    assert readiness_data["readiness_score"] == 94
    assert readiness_data["mpi_matched"] is True
    print("[PASS] 9. GET /api/intake/readiness-score/ML-9420-TX (94% Document Readability)")

    print("\nALL 9 PATIENT INTAKE & NOMINATION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_patient_intake_endpoints()
