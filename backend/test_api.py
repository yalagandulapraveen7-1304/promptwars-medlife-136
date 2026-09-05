import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from starlette.testclient import TestClient
from app.main import app

def run_tests():
    print("=== TESTING MEDLENS DASHBOARD BACKEND API ===")

    with TestClient(app) as client:
        # 1. Health Check
        res = client.get("/api/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("[PASS] GET /api/health ->", res.json())

        # 2. Dashboard Overview
        res = client.get("/api/dashboard/overview")
        assert res.status_code == 200, f"Overview failed: {res.text}"
        overview = res.json()
        print("[PASS] GET /api/dashboard/overview:")
        print(f"       Clinician: {overview['clinician']['name']} ({overview['clinician']['ward']})")
        print(f"       Active Roster: {overview['metrics']['active_inpatient_roster']}")
        print(f"       Pending Doctor Sign-off: {overview['metrics']['pending_doctor_signoff']}")
        print(f"       Flagged Inconsistencies: {overview['metrics']['flagged_inconsistencies']}")
        print(f"       Pipeline: {overview['pipeline']['file_name']} ({overview['pipeline']['parsed_percentage']}%)")

        # 3. Triage Queue - All
        res = client.get("/api/dashboard/triage-queue")
        assert res.status_code == 200, f"Triage queue failed: {res.text}"
        patients = res.json()
        assert len(patients) >= 3, "Expected at least 3 patients"
        print(f"[PASS] GET /api/dashboard/triage-queue -> Retrieved {len(patients)} patients")

        # 4. Triage Queue - Conflicts Filter
        res = client.get("/api/dashboard/triage-queue?filter=conflicts")
        assert res.status_code == 200
        conflict_patients = res.json()
        assert any(p["mrn"] == "ML-7920" for p in conflict_patients), "Expected Marcus Vance with conflict"
        print(f"[PASS] GET /api/dashboard/triage-queue?filter=conflicts -> {conflict_patients[0]['name']} flagged with conflict")

        # 5. Triage Queue - Out of Range Filter
        res = client.get("/api/dashboard/triage-queue?filter=out_of_range")
        assert res.status_code == 200
        oor_patients = res.json()
        assert any(p["mrn"] == "ML-8841" for p in oor_patients), "Expected Elena Rostova with out of range labs"
        print(f"[PASS] GET /api/dashboard/triage-queue?filter=out_of_range -> {oor_patients[0]['name']} has out-of-range labs")

        # 6. Triage Queue - Search Query
        res = client.get("/api/dashboard/triage-queue?q=HGB")
        assert res.status_code == 200
        search_patients = res.json()
        assert any(p["mrn"] == "ML-8841" for p in search_patients), "Search by lab code HGB failed"
        print(f"[PASS] GET /api/dashboard/triage-queue?q=HGB -> Found {search_patients[0]['name']}")

        # 7. Verify Lab Result
        res = client.post("/api/dashboard/verify-lab/ML-8841/HGB")
        assert res.status_code == 200
        verify_res = res.json()
        assert verify_res["success"] is True
        assert verify_res["lab"]["verified"] is True
        print(f"[PASS] POST /api/dashboard/verify-lab/ML-8841/HGB -> Lab verified: {verify_res['lab']['test_name']}, new pending count: {verify_res['updated_pending_count']}")

        # 8. Sync EHR
        res = client.post("/api/dashboard/sync-ehr")
        assert res.status_code == 200
        sync_res = res.json()
        assert sync_res["success"] is True
        print(f"[PASS] POST /api/dashboard/sync-ehr -> Synced at {sync_res['sync_time']}")

        # 9. Batch Sign-off
        res = client.post("/api/dashboard/batch-signoff")
        assert res.status_code == 200
        signoff_res = res.json()
        assert signoff_res["success"] is True
        print(f"[PASS] POST /api/dashboard/batch-signoff -> {signoff_res['message']}")

        print("\nALL 9 BACKEND API TESTS PASSED SUCCESSFULLY! [SUCCESS]")

if __name__ == "__main__":
    run_tests()
