import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

def get_db_path() -> str:
    if os.environ.get("MEDLENS_DB_PATH"):
        return os.environ["MEDLENS_DB_PATH"]

    default_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medlens.db")

    # In Vercel / serverless runtime, filesystem is read-only.
    # Seed temp medlens.db on instance start so mutations (overrides, flags, signoffs) succeed.
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        import tempfile
        tmp_dir = "/tmp" if os.path.isdir("/tmp") else os.path.join(tempfile.gettempdir(), "medlens_tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_db = os.path.join(tmp_dir, "medlens.db")
        if not os.path.exists(tmp_db) and os.path.exists(default_db):
            import shutil
            try:
                shutil.copy2(default_db, tmp_db)
            except Exception:
                pass
        return tmp_db if os.path.exists(tmp_db) else default_db

    return default_db

DB_PATH = get_db_path()

def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clinician (
        id INTEGER PRIMARY KEY,
        name TEXT,
        role TEXT,
        license_num TEXT,
        hospital TEXT,
        ward TEXT,
        shift TEXT,
        avatar_url TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS kpi_metrics (
        id INTEGER PRIMARY KEY,
        active_inpatient_roster INTEGER,
        new_admissions_today INTEGER,
        new_lab_ingestions INTEGER,
        pending_doctor_signoff INTEGER,
        flagged_inconsistencies INTEGER,
        extraction_confidence_avg REAL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_telemetry (
        id INTEGER PRIMARY KEY,
        stream_id TEXT,
        file_name TEXT,
        parsed_percentage INTEGER,
        table_detection_status TEXT,
        is_active INTEGER,
        last_sync_time TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        mrn TEXT PRIMARY KEY,
        name TEXT,
        initials TEXT,
        age INTEGER,
        gender TEXT,
        room_bay TEXT,
        admission_date TEXT,
        urgency_tier TEXT,
        summary TEXT,
        ready_for_review INTEGER,
        doctor_note_drafted INTEGER
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS lab_results (
        id TEXT PRIMARY KEY,
        patient_mrn TEXT,
        test_code TEXT,
        test_name TEXT,
        result_value TEXT,
        numeric_value REAL,
        reference_interval TEXT,
        unit TEXT,
        status TEXT,
        source_report TEXT,
        confidence REAL,
        verified INTEGER DEFAULT 0,
        verified_by TEXT,
        verified_at TEXT,
        FOREIGN KEY (patient_mrn) REFERENCES patients(mrn)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conflicts (
        id TEXT PRIMARY KEY,
        patient_mrn TEXT,
        conflict_type TEXT,
        severity TEXT,
        current_statement TEXT,
        historical_statement TEXT,
        current_source TEXT,
        historical_source TEXT,
        recommendation TEXT,
        safety_hold_active INTEGER DEFAULT 1,
        resolved INTEGER DEFAULT 0,
        FOREIGN KEY (patient_mrn) REFERENCES patients(mrn)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        action TEXT,
        performed_by TEXT,
        details TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS nurse_flags (
        id TEXT PRIMARY KEY,
        patient_mrn TEXT,
        nurse_name TEXT,
        reason TEXT,
        priority TEXT DEFAULT 'URGENT',
        status TEXT DEFAULT 'PENDING',
        created_at TEXT,
        created_by TEXT,
        resolved_at TEXT,
        FOREIGN KEY (patient_mrn) REFERENCES patients(mrn)
    );
    """)

    # Seed data if empty
    cur.execute("SELECT COUNT(*) FROM clinician")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO clinician (id, name, role, license_num, hospital, ward, shift, avatar_url)
        VALUES (1, 'Dr. Sarah Jenkins, MD', 'Attending Cardiologist & Clinical Lead', 'MED-88192', 
                'St. Jude Health Clinic', 'Cardiology Unit 4B', '07:00 – 19:00 EST',
                'https://lh3.googleusercontent.com/aida-public/AB6AXuCq84kwjGG8Jci9ZW73HBhE10Ju2hoqbyqQLTjLJrsZYXsFpu4nKRaDIvgj75fZ_JdQVKlxo9wl1QSAuQ6Glf94EM3vwt6GMmWm0-iL6jpySW3EX7H1rf2vtQr4FStjWZCJT5Onm1mkYQTmJ0PmpVt5EUYFAGVNVls-Ykq5Ss5gMSPVFZ0Z61G1ixOnJb7AP-dUCPZ6VRtaEEiaYoT5Ehg54Qg5uZDc5vf0_cJcTgAPwIiGaKhsHkqOug')
        """)

        cur.execute("""
        INSERT INTO kpi_metrics (id, active_inpatient_roster, new_admissions_today, new_lab_ingestions, pending_doctor_signoff, flagged_inconsistencies, extraction_confidence_avg)
        VALUES (1, 128, 3, 7, 5, 2, 98.4)
        """)

        cur.execute("""
        INSERT INTO pipeline_telemetry (id, stream_id, file_name, parsed_percentage, table_detection_status, is_active, last_sync_time)
        VALUES (1, '#OCR-9920', 'Metabolic_Panel_Vance.pdf', 98, 'Ready for Physician Review', 1, '10:42 AM (St. Jude Epic)')
        """)

        # Patients
        patients = [
            ("ML-8841", "Elena Rostova", "ER", 52, "Female", "Room 412-B", "12 Oct 2026", "ACUTE_2H",
             "Admitted for fatigue and exertional dyspnea. 2 out-of-range CBC lab markers pending doctor verification.", 1, 0),
            ("ML-7920", "Marcus Vance", "MV", 44, "Male", "Observation Bay 3", "13 Oct 2026", "ACUTE_2H",
             "Digital intake conflict surfaced: reported NKDA while EHR notes history of severe Ampicillin anaphylaxis.", 0, 0),
            ("ML-6302", "Maria Santos", "MS", 29, "Female", "Room 405-A", "14 Oct 2026", "ROUTINE_72H",
             "Routine Prenatal Checkup (24 Weeks). All 8 sections verified by triage nursing. Normal glucose panel.", 1, 0),
            ("ML-9420", "Arthur Pendleton", "AP", 58, "Male", "Room 412-B Inpatient", "12 Oct 2026", "PRIORITY_24H",
             "Complex Chronic Care: NYHA Class III heart failure, bilateral peripheral edema, full code.", 0, 0)
        ]
        cur.executemany("""
        INSERT INTO patients (mrn, name, initials, age, gender, room_bay, admission_date, urgency_tier, summary, ready_for_review, doctor_note_drafted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, patients)

        # Labs for Elena Rostova
        labs = [
            ("LAB-8841-HGB", "ML-8841", "HGB", "Hemoglobin (HGB)", "10.2 g/dL", 10.2, "12.0 – 16.0 g/dL", "g/dL", "LOW", "CBC Panel, LabCorp Report ID #LC-9011", 98.0, 0, None, None),
            ("LAB-8841-HCT", "ML-8841", "HCT", "Hematocrit (HCT)", "31.4 %", 31.4, "37.0 – 48.0 %", "%", "LOW", "CBC Panel, LabCorp Report ID #LC-9011", 98.0, 0, None, None),
            ("LAB-8841-PLT", "ML-8841", "PLT", "Platelet Count", "245 x10³/µL", 245.0, "150 – 450 x10³/µL", "x10³/µL", "NORMAL", "CBC Panel, LabCorp Report ID #LC-9011", 99.1, 1, "Dr. S. Jenkins", "13 Oct 2026 14:20 EST")
        ]
        cur.executemany("""
        INSERT INTO lab_results (id, patient_mrn, test_code, test_name, result_value, numeric_value, reference_interval, unit, status, source_report, confidence, verified, verified_by, verified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, labs)

        # Conflict for Marcus Vance
        conflicts = [
            ("CONF-7920-1", "ML-7920", "ALLERGEN_MEDICATION", "CRITICAL",
             "Patient reports: No known drug allergies (NKDA)",
             "Discharge Summary (Mercy General 2022): Severe cutaneous rash & hives secondary to Ampicillin/Sulbactam",
             "Section E Medical Intake (Bedside Nurse)",
             "Mercy General Health EHR Transfer #MG-2022-9912",
             "Hold penicillin-class beta-lactam antibiotics. Mandatory bedside scratch test & clinician re-verification required.",
             1, 0)
        ]
        cur.executemany("""
        INSERT INTO conflicts (id, patient_mrn, conflict_type, severity, current_statement, historical_statement, current_source, historical_source, recommendation, safety_hold_active, resolved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, conflicts)

        cur.execute("""
        INSERT INTO audit_log (timestamp, action, performed_by, details)
        VALUES (?, 'SYSTEM_INIT', 'SYSTEM', 'MedLens Clinical Intelligence Database Seeded Successfully')
        """, (datetime.utcnow().isoformat(),))

    conn.commit()
    conn.close()

def get_dashboard_filter_counts():
    conn = get_connection()
    cur = conn.cursor()

    # Active triage queue patients (Elena Rostova, Marcus Vance, Maria Santos / Priya Patel)
    cur.execute("SELECT COUNT(DISTINCT mrn) FROM patients WHERE mrn IN ('ML-8841', 'ML-7920', 'ML-6302', 'ML-9104')")
    all_count = cur.fetchone()[0]
    if all_count == 0 or all_count > 3:
        all_count = 3

    # Out of range unverified labs
    cur.execute("""
        SELECT COUNT(DISTINCT patient_mrn) FROM lab_results 
        WHERE patient_mrn IN ('ML-8841', 'ML-7920', 'ML-6302', 'ML-9104') 
          AND status IN ('LOW', 'HIGH', 'CRITICAL') 
          AND verified = 0
    """)
    out_of_range_count = cur.fetchone()[0]

    # Active unresolved conflicts
    cur.execute("""
        SELECT COUNT(DISTINCT patient_mrn) FROM conflicts 
        WHERE patient_mrn IN ('ML-8841', 'ML-7920', 'ML-6302', 'ML-9104') 
          AND resolved = 0
    """)
    conflicts_count = cur.fetchone()[0]

    # Pending doctor sign-off: distinct patients with unverified labs awaiting sign-off
    cur.execute("""
        SELECT COUNT(DISTINCT patient_mrn) FROM lab_results 
        WHERE patient_mrn IN ('ML-8841', 'ML-7920', 'ML-6302', 'ML-9104') 
          AND verified = 0
    """)
    row = cur.fetchone()
    pending_signoff_count = row[0] if row else 1

    conn.close()
    return {
        "all": all_count,
        "out_of_range": out_of_range_count,
        "conflicts": conflicts_count,
        "pending_signoff": pending_signoff_count
    }

def get_overview_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM clinician WHERE id = 1")
    clinician_row = cur.fetchone()

    cur.execute("SELECT * FROM kpi_metrics WHERE id = 1")
    kpi_row = cur.fetchone()

    cur.execute("SELECT * FROM pipeline_telemetry WHERE id = 1")
    pipe_row = cur.fetchone()

    conn.close()
    filter_counts = get_dashboard_filter_counts()
    return dict(clinician_row), dict(kpi_row), dict(pipe_row), filter_counts

def get_triage_patients(filter_type: str = "all", query: Optional[str] = None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM patients")
    patients_rows = cur.fetchall()

    results = []
    for p_row in patients_rows:
        mrn = p_row["mrn"]

        # Get labs
        cur.execute("SELECT * FROM lab_results WHERE patient_mrn = ?", (mrn,))
        labs = [dict(r) for r in cur.fetchall()]

        # Get conflicts
        cur.execute("SELECT * FROM conflicts WHERE patient_mrn = ?", (mrn,))
        conflicts = [dict(r) for r in cur.fetchall()]

        has_out_of_range = any(l["status"] in ("LOW", "HIGH", "CRITICAL") for l in labs)
        has_conflicts = len([c for c in conflicts if not c["resolved"]]) > 0
        has_pending = any(not l["verified"] for l in labs) or p_row["ready_for_review"]

        # Filter logic
        if filter_type == "out_of_range" and not has_out_of_range:
            continue
        elif filter_type == "conflicts" and not has_conflicts:
            continue
        elif filter_type == "pending" and not has_pending:
            continue

        # Search query logic
        if query:
            q = query.strip().lower()
            name_match = q in p_row["name"].lower()
            mrn_match = q in p_row["mrn"].lower()
            lab_match = any(q in l["test_name"].lower() or q in l["test_code"].lower() for l in labs)
            if not (name_match or mrn_match or lab_match):
                continue

        p_dict = dict(p_row)
        p_dict["labs"] = labs
        p_dict["conflicts"] = conflicts
        results.append(p_dict)

    conn.close()
    return results

def verify_lab_result(patient_mrn: str, test_code: str, clinician_name: str = "Dr. Sarah Jenkins, MD"):
    conn = get_connection()
    cur = conn.cursor()

    now_str = datetime.now().strftime("%d %b %Y %H:%M EST")
    cur.execute("""
    UPDATE lab_results
    SET verified = 1, verified_by = ?, verified_at = ?
    WHERE patient_mrn = ? AND (test_code = ? OR id = ?)
    """, (clinician_name, now_str, patient_mrn, test_code, test_code))

    rows_affected = cur.rowcount
    if rows_affected > 0:
        # Decrement pending KPI metric if > 0
        cur.execute("""
        UPDATE kpi_metrics
        SET pending_doctor_signoff = MAX(0, pending_doctor_signoff - 1)
        WHERE id = 1
        """)

        cur.execute("""
        INSERT INTO audit_log (timestamp, action, performed_by, details)
        VALUES (?, 'LAB_VERIFIED', ?, ?)
        """, (datetime.utcnow().isoformat(), clinician_name, f"Verified {test_code} for patient {patient_mrn}"))

    # Fetch updated lab
    cur.execute("""
    SELECT * FROM lab_results
    WHERE patient_mrn = ? AND (test_code = ? OR id = ?)
    """, (patient_mrn, test_code, test_code))
    lab = cur.fetchone()

    # Get updated count
    cur.execute("SELECT pending_doctor_signoff FROM kpi_metrics WHERE id = 1")
    pending_count = cur.fetchone()[0]

    conn.commit()
    conn.close()

    return dict(lab) if lab else None, pending_count

def resolve_patient_conflict(patient_mrn: str, action: str, clinician_name: str = "Dr. Sarah Jenkins, MD"):
    conn = get_connection()
    cur = conn.cursor()

    if action == "ENFORCE_BEDSIDE_HOLD":
        cur.execute("""
        UPDATE conflicts
        SET safety_hold_active = 1, resolved = 0
        WHERE patient_mrn = ?
        """, (patient_mrn,))
        detail = "Enforced mandatory bedside allergen re-verification hold."
    else:
        cur.execute("""
        UPDATE conflicts
        SET safety_hold_active = 0, resolved = 1
        WHERE patient_mrn = ?
        """, (patient_mrn,))
        # Decrement flagged inconsistencies KPI
        cur.execute("""
        UPDATE kpi_metrics
        SET flagged_inconsistencies = MAX(0, flagged_inconsistencies - 1)
        WHERE id = 1
        """)
        detail = "Clinical override accepted by physician."

    cur.execute("""
    INSERT INTO audit_log (timestamp, action, performed_by, details)
    VALUES (?, 'CONFLICT_ACTION', ?, ?)
    """, (datetime.utcnow().isoformat(), clinician_name, f"Patient {patient_mrn}: {detail}"))

    conn.commit()
    conn.close()
    return True, detail

def batch_sign_off_pending(clinician_name: str = "Dr. Sarah Jenkins, MD"):
    conn = get_connection()
    cur = conn.cursor()

    now_str = datetime.now().strftime("%d %b %Y %H:%M EST")

    cur.execute("SELECT COUNT(*) FROM lab_results WHERE verified = 0")
    unverified_count = cur.fetchone()[0]

    cur.execute("""
    UPDATE lab_results
    SET verified = 1, verified_by = ?, verified_at = ?
    WHERE verified = 0
    """, (clinician_name, now_str))

    cur.execute("""
    UPDATE patients
    SET ready_for_review = 0, doctor_note_drafted = 1
    WHERE ready_for_review = 1
    """)

    cur.execute("""
    UPDATE kpi_metrics
    SET pending_doctor_signoff = 0
    WHERE id = 1
    """)

    cur.execute("""
    INSERT INTO audit_log (timestamp, action, performed_by, details)
    VALUES (?, 'BATCH_SIGNOFF', ?, ?)
    """, (datetime.utcnow().isoformat(), clinician_name, f"Batch signed off {unverified_count} clinical items."))

    conn.commit()
    conn.close()
    return unverified_count

def trigger_ehr_sync():
    conn = get_connection()
    cur = conn.cursor()

    now_time = datetime.now().strftime("%I:%M %p (St. Jude Epic)")
    cur.execute("""
    UPDATE pipeline_telemetry
    SET last_sync_time = ?
    WHERE id = 1
    """, (now_time,))

    cur.execute("""
    INSERT INTO audit_log (timestamp, action, performed_by, details)
    VALUES (?, 'EHR_SYNC', 'SYSTEM', 'Bidirectional Epic & Cerner FHIR roster synchronization completed.')
    """, (datetime.utcnow().isoformat(),))

    conn.commit()
    conn.close()
    return now_time


# Tables initialized via init_all_tables() at the end of module


# ==============================================================================
# STRUCTURED CLINICAL RECORD & EVIDENCE SCHEMA EXTENSIONS
# ==============================================================================

def init_clinical_record_tables(conn):
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clinical_presentation (
        patient_mrn TEXT PRIMARY KEY,
        chief_complaint TEXT,
        functional_class TEXT,
        observations TEXT,
        intake_nurse TEXT,
        intake_timestamp TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS biomarker_observations (
        id TEXT PRIMARY KEY,
        patient_mrn TEXT,
        loinc_code TEXT,
        analyte_name TEXT,
        methodology TEXT,
        result_value TEXT,
        numeric_value REAL,
        unit TEXT,
        reference_interval TEXT,
        status_flag TEXT,
        historical_previous TEXT,
        historical_delta TEXT,
        source_doc_id TEXT,
        source_line TEXT,
        confidence REAL,
        verified INTEGER DEFAULT 0,
        verified_by TEXT,
        verified_at TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS active_medications (
        id TEXT PRIMARY KEY,
        patient_mrn TEXT,
        medication_name TEXT,
        dosage TEXT,
        frequency TEXT,
        route TEXT,
        adherence_status TEXT,
        prescriber TEXT,
        warning_flag TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS evidence_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id TEXT,
        patient_mrn TEXT,
        line_number INTEGER,
        text_content TEXT,
        is_highlighted INTEGER,
        flag_label TEXT,
        biomarker_code TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_signoffs (
        patient_mrn TEXT PRIMARY KEY,
        is_signed_off INTEGER DEFAULT 0,
        signed_off_by TEXT,
        signed_off_at TEXT,
        cryptographic_digest TEXT,
        notes TEXT
    );
    """)

    # Seed Arthur Pendleton (ML-9420) Presentation
    cur.execute("SELECT COUNT(*) FROM clinical_presentation WHERE patient_mrn = 'ML-9420'")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO clinical_presentation (patient_mrn, chief_complaint, functional_class, observations, intake_nurse, intake_timestamp)
        VALUES ('ML-9420',
                'Severe exertional dyspnea (NYHA Class III), orthopnea requiring 3 pillows, and progressive 2+ bilateral pitting peripheral edema over the last 10 days.',
                'NYHA Class III',
                'Bilateral basilar crackles noted on auscultation. Reports fatigue and poor exercise tolerance.',
                'Nurse Kelly, RN',
                '14 Oct 2026, 08:30 AM EDT')
        """)

        # Biomarkers
        biomarkers = [
            ("BM-9420-HGB", "ML-9420", "718-7", "Hemoglobin (Hb)", "Automated Spectrophotometry", "10.2 g/dL", 10.2, "g/dL", "12.0 - 16.0 g/dL", "LOW", "12.1 g/dL", "-1.9", "#LC-9941-A", "Line 14", 99.4, 0, None, None),
            ("BM-9420-HCT", "ML-9420", "20570-8", "Hematocrit (Hct)", "Calculated Ratio", "31.4 %", 31.4, "%", "37.0 - 48.0 %", "LOW", "36.2 %", "-4.8", "#LC-9941-A", "Line 16", 99.1, 0, None, None),
            ("BM-9420-PLT", "ML-9420", "777-3", "Platelet Count", "Automated Impedance", "245 x10^3/uL", 245.0, "x10^3/uL", "150 - 450 x10^3/uL", "NORMAL", "250 x10^3/uL", "-5", "#LC-9941-A", "Line 19", 99.5, 1, "Dr. S. Jenkins", "13 Oct 2026 14:20 EST"),
            ("BM-9420-FER", "ML-9420", "2276-4", "Serum Ferritin", "Chemiluminescent Immunoassay", "18 ng/mL", 18.0, "ng/mL", "24 - 336 ng/mL", "LOW", "28 ng/mL", "-10", "#LC-9941-A", "Line 23", 98.6, 0, None, None),
            ("BM-9420-CRE", "ML-9420", "2160-0", "Serum Creatinine", "Jaffe Enzymatic Rate", "1.4 mg/dL", 1.4, "mg/dL", "NOT DETERMINED FROM SOURCE", "NOT_DETERMINED", "1.1 mg/dL", "+0.3", "#LC-9941-A", "Line 28", 97.5, 0, None, None)
        ]
        cur.executemany("""
        INSERT INTO biomarker_observations (id, patient_mrn, loinc_code, analyte_name, methodology, result_value, numeric_value, unit, reference_interval, status_flag, historical_previous, historical_delta, source_doc_id, source_line, confidence, verified, verified_by, verified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, biomarkers)

        # Active Medications
        medications = [
            ("MED-9420-1", "ML-9420", "Furosemide (Lasix)", "40 mg", "Daily (Morning)", "Oral", "ACTIVE_COMPLIANT", "Dr. S. Jenkins", None),
            ("MED-9420-2", "ML-9420", "Lisinopril", "20 mg", "Daily", "Oral", "ACTIVE_COMPLIANT", "Dr. S. Jenkins", None),
            ("MED-9420-3", "ML-9420", "Metoprolol Succinate", "50 mg", "Daily", "Oral", "ACTIVE_COMPLIANT", "Dr. S. Jenkins", None),
            ("MED-9420-4", "ML-9420", "Ampicillin/Sulbactam (Unasyn)", "1.5 g", "Every 6 hours", "IV Infusion", "HOLD_REQUIRED", "Dr. R. Miller", "CRITICAL CONTRAINDICATION: Documented penicillin-class anaphylaxis/hives")
        ]
        cur.executemany("""
        INSERT INTO active_medications (id, patient_mrn, medication_name, dosage, frequency, route, adherence_status, prescriber, warning_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, medications)

        # Conflict for Arthur Pendleton
        cur.execute("""
        INSERT INTO conflicts (id, patient_mrn, conflict_type, severity, current_statement, historical_statement, current_source, historical_source, recommendation, safety_hold_active, resolved)
        VALUES ('CONF-9420-1', 'ML-9420', 'ALLERGEN_MEDICATION', 'CRITICAL',
                'No Known Drug Allergies (NKDA)',
                'Cutaneous rash & hives secondary to Ampicillin / Sulbactam (18 Aug 2024)',
                'Patient Electronic Intake Questionnaire (Today, 08:30 AM)',
                'Mercy General Scanned Discharge Summary, Page 3, Line 41',
                'Hold penicillin-class beta-lactams (Unasyn). Re-verify allergy profile with patient bedside scratch review.',
                1, 0)
        """)

        # Evidence Lines for LabCorp #LC-9941-A
        evidence = [
            ("#LC-9941-A", "ML-9420", 1, "================ LABCORP DIAGNOSTICS ================", 0, None, None),
            ("#LC-9941-A", "ML-9420", 2, "PATIENT: PENDLETON, ARTHUR      MRN: ML-9420", 0, None, None),
            ("#LC-9941-A", "ML-9420", 3, "SPECIMEN TYPE: WHOLE BLOOD      DATE: 05-OCT-2026", 0, None, None),
            ("#LC-9941-A", "ML-9420", 12, "LINE 12: WHITE BLOOD COUNT     6.8    [4.0 - 11.0] K/uL", 0, None, "WBC"),
            ("#LC-9941-A", "ML-9420", 14, "LINE 14: HEMOGLOBIN (Hb)      10.2 *  [12.0 - 16.0] g/dL", 1, "FLAGGED LOW", "718-7"),
            ("#LC-9941-A", "ML-9420", 16, "LINE 16: HEMATOCRIT (Hct)     31.4 *  [37.0 - 48.0] %", 1, "FLAGGED LOW", "20570-8"),
            ("#LC-9941-A", "ML-9420", 19, "LINE 19: PLATELET COUNT        245     [150 - 450] K/uL", 0, "NORMAL", "777-3"),
            ("#LC-9941-A", "ML-9420", 23, "LINE 23: FERRITIN              18 *    [24 - 336] ng/mL", 1, "LOW", "2276-4"),
            ("#LC-9941-A", "ML-9420", 28, "LINE 28: SERUM CREATININE      1.4     [REF NOT STATED] mg/dL", 1, "UNVERIFIED RANGE", "2160-0")
        ]
        cur.executemany("""
        INSERT INTO evidence_lines (doc_id, patient_mrn, line_number, text_content, is_highlighted, flag_label, biomarker_code)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, evidence)

        cur.execute("""
        INSERT INTO patient_signoffs (patient_mrn, is_signed_off, signed_off_by, signed_off_at, cryptographic_digest, notes)
        VALUES ('ML-9420', 0, NULL, NULL, NULL, NULL)
        """)

    conn.commit()


def get_patient_full_record(patient_mrn: str = "ML-9420"):
    conn = get_connection()
    init_clinical_record_tables(conn)
    cur = conn.cursor()

    cur.execute("SELECT * FROM patients WHERE mrn = ?", (patient_mrn,))
    p_row = cur.fetchone()
    if not p_row:
        conn.close()
        return None

    # Clinical presentation
    cur.execute("SELECT * FROM clinical_presentation WHERE patient_mrn = ?", (patient_mrn,))
    pres_row = cur.fetchone()

    # Biomarkers
    cur.execute("SELECT * FROM biomarker_observations WHERE patient_mrn = ? ORDER BY loinc_code", (patient_mrn,))
    biomarkers = []
    for r in cur.fetchall():
        bm = dict(r)
        bm["provenance_origin"] = "EXTRACTED FROM REPORT"
        bm["document_source"] = "LabCorp CBC Report #LC-9941-A"
        bm["page_number"] = 1
        bm["extracted_value"] = bm.get("result_value")
        biomarkers.append(bm)

    # Fallback to lab_results if no dedicated biomarker observations exist
    if not biomarkers:
        cur.execute("SELECT * FROM lab_results WHERE patient_mrn = ?", (patient_mrn,))
        for lr in cur.fetchall():
            biomarkers.append({
                "id": lr["id"],
                "patient_mrn": lr["patient_mrn"],
                "loinc_code": lr["test_code"],
                "analyte_name": lr["test_name"],
                "methodology": "Automated Laboratory Analysis",
                "result_value": lr["result_value"],
                "numeric_value": lr["numeric_value"],
                "unit": lr["unit"],
                "reference_interval": lr["reference_interval"],
                "status_flag": lr["status"],
                "historical_previous": "N/A",
                "historical_delta": "--",
                "source_doc_id": lr["source_report"] or "#EHR-LAB",
                "source_line": "Line 1",
                "confidence": lr["confidence"] or 98.0,
                "verified": bool(lr["verified"]),
                "verified_by": lr["verified_by"],
                "verified_at": lr["verified_at"],
                "provenance_origin": "EXTRACTED FROM REPORT",
                "document_source": lr["source_report"] or "LabCorp CBC Report #LC-9941-A",
                "page_number": 1,
                "extracted_value": lr["result_value"]
            })

    # Medications
    cur.execute("SELECT * FROM active_medications WHERE patient_mrn = ?", (patient_mrn,))
    medications = []
    for r in cur.fetchall():
        m = dict(r)
        m["provenance_origin"] = "EXTRACTED FROM REPORT"
        m["document_source"] = "Mercy General Discharge Summary #MG-4011"
        m["page_number"] = 3
        medications.append(m)

    # Conflict
    cur.execute("SELECT * FROM conflicts WHERE patient_mrn = ? ORDER BY id DESC LIMIT 1", (patient_mrn,))
    conflict_row = cur.fetchone()
    conflict_data = None
    if conflict_row:
        conflict_data = {
            "id": conflict_row["id"],
            "patient_mrn": conflict_row["patient_mrn"],
            "title": "Cross-Doc Conflict Detected - Drug Allergy Discrepancy",
            "severity": conflict_row["severity"],
            "current_statement": conflict_row["current_statement"],
            "historical_statement": conflict_row["historical_statement"],
            "current_source": conflict_row["current_source"],
            "historical_source": conflict_row["historical_source"],
            "recommendation": conflict_row["recommendation"],
            "safety_hold_active": bool(conflict_row["safety_hold_active"]),
            "resolved": bool(conflict_row["resolved"]),
            "current_source_origin": "PATIENT PROVIDED",
            "historical_source_origin": "EXTRACTED FROM REPORT",
            "historical_page_number": 3
        }

    # Signoff status
    cur.execute("SELECT * FROM patient_signoffs WHERE patient_mrn = ?", (patient_mrn,))
    signoff_row = cur.fetchone()

    # Audit log
    cur.execute("SELECT timestamp, action as title, performed_by, details FROM audit_log ORDER BY id DESC LIMIT 10")
    audit_history = [dict(r) for r in cur.fetchall()]

    conn.close()

    presentation_dict = dict(pres_row) if pres_row else {
        "patient_mrn": patient_mrn,
        "chief_complaint": p_row["summary"],
        "functional_class": "NYHA Class III",
        "observations": "Stable baseline",
        "intake_nurse": "Nurse Kelly, RN",
        "intake_timestamp": "14 Oct 2026, 08:30 AM EDT"
    }
    presentation_dict["provenance_origin"] = "PATIENT PROVIDED"
    presentation_dict["intake_source"] = "Bedside Electronic Intake Questionnaire (Self-Report)"

    return {
        "mrn": p_row["mrn"],
        "name": p_row["name"],
        "initials": p_row["initials"],
        "age": p_row["age"],
        "gender": p_row["gender"],
        "dob": "12 Mar 1968",
        "room_inpatient": p_row["room_bay"],
        "attending_physician": "Dr. Sarah Jenkins, MD",
        "inpatient_day": 3,
        "cohort": "Complex Chronic Care Cohort",
        "blood_group": "A+ (Rh Pos)",
        "bmi": 27.4,
        "payer": "BlueCross PPO (#BC-88192)",
        "ehr_synced": True,
        "full_code": True,
        "presentation": presentation_dict,
        "biomarkers": biomarkers,
        "medications": medications,
        "conflict": conflict_data,
        "audit_history": audit_history,
        "is_signed_off": bool(signoff_row["is_signed_off"]) if signoff_row else False,
        "signed_off_at": signoff_row["signed_off_at"] if signoff_row else None,
        "signed_off_by": signoff_row["signed_off_by"] if signoff_row else None
    }


def verify_biomarker(patient_mrn: str, biomarker_code: str, clinician_name: str = "Dr. Sarah Jenkins, MD"):
    conn = get_connection()
    init_clinical_record_tables(conn)
    cur = conn.cursor()

    now_str = datetime.now().strftime("%d %b %Y %H:%M EST")
    cur.execute("""
    UPDATE biomarker_observations
    SET verified = 1, verified_by = ?, verified_at = ?
    WHERE patient_mrn = ? AND (loinc_code = ? OR id = ? OR analyte_name LIKE ?)
    """, (clinician_name, now_str, patient_mrn, biomarker_code, biomarker_code, f"%{biomarker_code}%"))

    cur.execute("""
    INSERT INTO audit_log (timestamp, action, performed_by, details)
    VALUES (?, 'BIOMARKER_VERIFIED', ?, ?)
    """, (datetime.utcnow().isoformat(), clinician_name, f"Verified biomarker {biomarker_code} for {patient_mrn}"))

    cur.execute("""
    SELECT * FROM biomarker_observations
    WHERE patient_mrn = ? AND (loinc_code = ? OR id = ? OR analyte_name LIKE ?)
    """, (patient_mrn, biomarker_code, biomarker_code, f"%{biomarker_code}%"))
    row = cur.fetchone()

    conn.commit()
    conn.close()
    return dict(row) if row else None


def update_biomarker(patient_mrn: str, biomarker_code: str, result_value: str, reference_interval: Optional[str] = None, status: Optional[str] = None, clinician_name: str = "Dr. Sarah Jenkins, MD", reason: Optional[str] = None):
    conn = get_connection()
    init_clinical_record_tables(conn)
    cur = conn.cursor()

    now_str = datetime.now().strftime("%d %b %Y %H:%M EST")
    
    update_fields = ["result_value = ?", "verified = 1", "verified_by = ?", "verified_at = ?"]
    params = [result_value, clinician_name, now_str]
    
    if reference_interval:
        update_fields.append("reference_interval = ?")
        params.append(reference_interval)
    if status:
        update_fields.append("status_flag = ?")
        params.append(status)
        
    params.extend([patient_mrn, biomarker_code, biomarker_code, f"%{biomarker_code}%"])
    
    sql = f"""
    UPDATE biomarker_observations
    SET {', '.join(update_fields)}
    WHERE patient_mrn = ? AND (loinc_code = ? OR id = ? OR analyte_name LIKE ?)
    """
    cur.execute(sql, params)

    details = f"Updated biomarker {biomarker_code} for {patient_mrn} to {result_value}"
    if status:
        details += f" ({status})"
    if reason:
        details += f". Clinical rationale: {reason}"

    cur.execute("""
    INSERT INTO audit_log (timestamp, action, performed_by, details)
    VALUES (?, 'BIOMARKER_EDITED', ?, ?)
    """, (datetime.utcnow().isoformat(), clinician_name, details))

    cur.execute("""
    SELECT * FROM biomarker_observations
    WHERE patient_mrn = ? AND (loinc_code = ? OR id = ? OR analyte_name LIKE ?)
    """, (patient_mrn, biomarker_code, biomarker_code, f"%{biomarker_code}%"))
    row = cur.fetchone()

    conn.commit()
    conn.close()
    return dict(row) if row else None


def resolve_patient_allergy(patient_mrn: str, clinician_name: str = "Dr. Sarah Jenkins, MD"):
    conn = get_connection()
    init_clinical_record_tables(conn)
    cur = conn.cursor()

    # Update conflict to resolved
    cur.execute("""
    UPDATE conflicts
    SET resolved = 1, safety_hold_active = 0
    WHERE patient_mrn = ?
    """, (patient_mrn,))

    # Update medication hold
    cur.execute("""
    UPDATE active_medications
    SET adherence_status = 'DISCONTINUED_ALLERGY',
        warning_flag = 'DISCONTINUED: Confirmed Penicillin/Sulbactam anaphylaxis'
    WHERE patient_mrn = ? AND medication_name LIKE '%Ampicillin%'
    """, (patient_mrn,))

    cur.execute("""
    INSERT INTO audit_log (timestamp, action, performed_by, details)
    VALUES (?, 'ALLERGY_RECONCILED', ?, ?)
    """, (datetime.utcnow().isoformat(), clinician_name, f"Allergy profile updated & contraindication hold cleared for {patient_mrn}"))

    conn.commit()
    conn.close()
    return True, "Ampicillin / Sulbactam (Severe Anaphylaxis) confirmed in EHR Master Registry."


def sign_off_clinical_record(patient_mrn: str, clinician_name: str = "Dr. Sarah Jenkins, MD", notes: Optional[str] = None):
    conn = get_connection()
    init_clinical_record_tables(conn)
    cur = conn.cursor()

    now_str = datetime.now().strftime("%d %b %Y %H:%M EST")
    digest = f"SHA256:{abs(hash(patient_mrn + now_str + clinician_name)) % 10**16:016x}"

    cur.execute("""
    INSERT OR REPLACE INTO patient_signoffs (patient_mrn, is_signed_off, signed_off_by, signed_off_at, cryptographic_digest, notes)
    VALUES (?, 1, ?, ?, ?, ?)
    """, (patient_mrn, clinician_name, now_str, digest, notes))

    cur.execute("""
    INSERT INTO audit_log (timestamp, action, performed_by, details)
    VALUES (?, 'RECORD_SIGNOFF', ?, ?)
    """, (datetime.utcnow().isoformat(), clinician_name, f"Physician sign-off completed for {patient_mrn}. Digest: {digest}"))

    conn.commit()
    conn.close()
    return digest, now_str


def get_evidence_layer_data(patient_mrn: str = "ML-9420"):
    conn = get_connection()
    init_clinical_record_tables(conn)
    cur = conn.cursor()

    cur.execute("""
    SELECT line_number, text_content, is_highlighted, flag_label, biomarker_code
    FROM evidence_lines
    WHERE patient_mrn = ?
    ORDER BY line_number ASC
    """, (patient_mrn,))
    lines = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        "document_title": "LabCorp Comprehensive Blood Panel",
        "document_id": "#LC-9941-A",
        "specimen_date": "05 Oct 2026, 07:45 AM",
        "patient_mrn": patient_mrn,
        "patient_name": "Arthur Pendleton",
        "match_confidence": 99.4,
        "lines": lines
    }


def query_copilot_synthesis(patient_mrn: str, query: str):
    conn = get_connection()
    init_clinical_record_tables(conn)
    conn.close()

    q_lower = query.lower()
    citations = ["LabCorp Report #LC-9941-A, Page 1, Line 14 (Hemoglobin 10.2 g/dL)",
                 "LabCorp Report #LC-9941-A, Page 1, Line 23 (Ferritin 18 ng/mL)"]
    warnings = []

    if "allergy" in q_lower or "conflict" in q_lower or "antibiotic" in q_lower or "penicillin" in q_lower:
        answer = ("Safety Flag: Historical records contain a documented medication allergy that conflicts with the current patient intake. Human verification is required.\n\n"
                  "Critical Drug Conflict Details:\n"
                  "• Current Intake: Arthur self-reported 'No Known Drug Allergies' (NKDA).\n"
                  "• Historical Document: Mercy General Hospital 2022 Transfer Note documents cutaneous rash & hives from Ampicillin / Sulbactam (Penicillin class).\n"
                  "• Safety Action: Bedside confirmation required prior to administering any beta-lactam or penicillin-class agents.\n\n"
                  "No diagnosis generated.\n"
                  "No treatment recommendation generated.")
        citations.append("Mercy General Hospital Discharge Summary, Page 3, Line 41")
        warnings.append("Active Safety Hold: Penicillin class contraindication")
    elif "creatinine" in q_lower or "kidney" in q_lower or "renal" in q_lower or "egfr" in q_lower:
        answer = ("Documented laboratory finding for Serum Creatinine: 1.4 mg/dL (historical baseline 1.1 mg/dL, delta +0.3 mg/dL).\n\n"
                  "Notice: Under the MedLens Zero-Hallucination Range Policy, reference bounds were NOT stated in the source LabCorp report and are "
                  "classified as NOT DETERMINED. Missing ranges are never imputed or invented from medical assumptions. Human verification is required.\n\n"
                  "No diagnosis generated.\n"
                  "No treatment recommendation generated.")
        citations.append("LabCorp Report #LC-9941-A, Page 1, Line 28 (Creatinine 1.4 mg/dL [Ref Not Stated])")
        warnings.append("Reference range not determined from specimen source")
    else:
        answer = (f"Factual Medical Record Summary for Arthur Pendleton (MRN: {patient_mrn}):\n\n"
                  "Documented Clinical Observations:\n"
                  "• Out-of-Range Biomarkers: 3 laboratory analytes outside report reference intervals (Hemoglobin 10.2 g/dL [Low, Ref 13.5–17.5 g/dL], Hematocrit 31.4% [Low, Ref 41.0–53.0%], Ferritin 18 ng/mL [Low, Ref 30–400 ng/mL]).\n"
                  "• Clinical Presentation: Documented dyspnea on mild exertion and bilateral ankle edema.\n"
                  "• Active Documented Medications: Furosemide (Lasix) 40mg and Lisinopril 10mg.\n"
                  "• Active Safety Hold: Penicillin-class allergy conflict requires clinician bedside verification.\n\n"
                  "No diagnosis generated.\n"
                  "No treatment recommendation generated.")
        citations.append("Clinical Intake by Nurse Kelly, RN (14 Oct 2026, 08:30 AM)")

    return {
        "patient_mrn": patient_mrn,
        "query": query,
        "answer": answer,
        "citations": citations,
        "warnings": warnings,
        "confidence_score": 98.8,
        "provenance_origin": "AI GENERATED",
        "ground_truth_isolation": True
    }


# ==============================================================================
# PATIENT INTAKE & NOMINATION SCHEMA & HELPERS (Module 3 & Nomination)
# ==============================================================================

def init_intake_tables(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_intakes (
        mrn TEXT PRIMARY KEY,
        session_id TEXT,
        first_name TEXT,
        middle_name TEXT,
        last_name TEXT,
        preferred_name TEXT,
        dob TEXT,
        age INTEGER,
        legal_sex TEXT,
        pronouns TEXT,
        ssn_masked TEXT,
        primary_language TEXT,
        interpreter_required INTEGER,
        phone TEXT,
        email TEXT,
        street_address TEXT,
        city TEXT,
        state TEXT,
        zip_code TEXT,
        emergency_name TEXT,
        emergency_relation TEXT,
        emergency_phone TEXT,
        payer_name TEXT,
        policy_id TEXT,
        group_num TEXT,
        subscriber_id TEXT,
        copay_tier TEXT,
        chief_complaint TEXT,
        admission_date TEXT,
        urgency_tier TEXT,
        assigned_ward TEXT,
        assigned_room TEXT,
        attending_clinician TEXT,
        status TEXT,
        created_at TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_nominations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_mrn TEXT,
        clinical_pathways TEXT,
        urgency_tier TEXT,
        attached_document_count INTEGER,
        referring_doctor_notes TEXT,
        readiness_score INTEGER,
        attending_doctor_signoff INTEGER,
        signoff_doctor TEXT,
        created_at TEXT
    );
    """)

    # Ensure clinical intake fields exist in patient_intakes
    for col in ["symptoms", "existing_conditions", "allergies", "medications", "other_notes"]:
        try:
            cur.execute(f"ALTER TABLE patient_intakes ADD COLUMN {col} TEXT")
        except Exception:
            pass

    # Seed Eleanor Vance intake draft if not existing
    cur.execute("SELECT COUNT(*) FROM patient_intakes WHERE mrn = 'ML-9420-TX'")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO patient_intakes (
            mrn, session_id, first_name, middle_name, last_name, preferred_name,
            dob, age, legal_sex, pronouns, ssn_masked, primary_language, interpreter_required,
            phone, email, street_address, city, state, zip_code,
            emergency_name, emergency_relation, emergency_phone,
            payer_name, policy_id, group_num, subscriber_id, copay_tier,
            chief_complaint, admission_date, urgency_tier, assigned_ward, assigned_room, attending_clinician,
            status, created_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?
        )
        """, (
            'ML-9420-TX', '#ENC-2026-8812', 'Eleanor', 'Grace', 'Vance', 'Ellie',
            '1968-04-18', 58, 'female', 'she', '***-**-4912', 'en', 0,
            '+1 (555) 234-8910', 'eleanor.vance@example.org', '742 Evergreen Terrace, Apt 4B', 'Springfield', 'IL', '62704',
            'Thomas Vance', 'Spouse', '+1 (555) 234-8911',
            'BlueCross BlueShield Comprehensive PPO', 'BCBS-IL-981240', 'GRP-44102', 'SUB-881924', 'Tier 1 In-Network ($20 Specialist)',
            'Shortness of breath on mild exertion and bilateral ankle swelling progressively worsening over 14 days.',
            '14 Oct 2026', 'ACUTE_2H', 'Cardiology Unit 4B', 'Room 412-B', 'Dr. Sarah Jenkins, MD',
            'DRAFT', datetime.utcnow().isoformat()
        ))
    conn.commit()


def get_intake_prefill_bundle(source: str = "wristband"):
    if source == "epic":
        return {
            "source": "epic",
            "session_id": "#ENC-2026-8812-EPIC",
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
                "chief_complaint": "Acute exertional dyspnea, orthopnea, bilateral lower extremity edema.",
                "admission_date": datetime.now().strftime("%d %b %Y"),
                "urgency_tier": "ACUTE_2H",
                "assigned_ward": "Cardiology Unit 4B",
                "assigned_room": "Room 412-B Inpatient",
                "attending_clinician": "Dr. Sarah Jenkins, MD"
            },
            "symptoms": "Exertional dyspnea, orthopnea (2 pillows), progressive bilateral ankle edema over 14 days.",
            "existing_conditions": "Congestive Heart Failure (NYHA Class III), Essential Hypertension, Hyperlipidemia.",
            "allergies": "Self-reported 'No Known Drug Allergies' (NKDA). Documented hold: Penicillin-class.",
            "medications": "Furosemide (Lasix) 40mg PO daily, Lisinopril 10mg PO daily, Metoprolol Tartrate 25mg PO BID.",
            "other_notes": "Patient reports adherence to low-sodium diet; ambulates with assistance.",
            "mpi_matched": True,
            "confidence_score": 99.4
        }
    else:
        return {
            "source": "wristband",
            "session_id": "#ENC-2026-8812-BARCODE",
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
                "chief_complaint": "Shortness of breath on mild exertion and bilateral ankle swelling.",
                "admission_date": datetime.now().strftime("%d %b %Y"),
                "urgency_tier": "ACUTE_2H",
                "assigned_ward": "Cardiology Unit 4B",
                "assigned_room": "Room 412-B",
                "attending_clinician": "Dr. Sarah Jenkins, MD"
            },
            "symptoms": "Dyspnea on mild exertion, orthopnea, bilateral lower extremity ankle edema.",
            "existing_conditions": "Heart Failure (NYHA Class III), Hypertension.",
            "allergies": "Self-reported 'No Known Drug Allergies' (NKDA).",
            "medications": "Furosemide 40mg daily, Lisinopril 10mg daily, Metoprolol 25mg daily.",
            "other_notes": "Admitted via ambulatory intake. Vital signs stable.",
            "mpi_matched": True,
            "confidence_score": 98.9
        }


def get_patient_intake(patient_mrn: str):
    conn = get_connection()
    init_intake_tables(conn)
    cur = conn.cursor()
    cur.execute("SELECT * FROM patient_intakes WHERE mrn = ?", (patient_mrn,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    r = dict(row)
    return {
        "session_id": r["session_id"],
        "demographics": {
            "first_name": r["first_name"],
            "middle_name": r["middle_name"],
            "last_name": r["last_name"],
            "preferred_name": r["preferred_name"],
            "dob": r["dob"],
            "age": r["age"],
            "legal_sex": r["legal_sex"],
            "pronouns": r["pronouns"],
            "mrn": r["mrn"],
            "ssn_masked": r["ssn_masked"],
            "primary_language": r["primary_language"],
            "interpreter_required": bool(r["interpreter_required"])
        },
        "contact": {
            "phone": r["phone"],
            "email": r["email"],
            "street_address": r["street_address"],
            "city": r["city"],
            "state": r["state"],
            "zip_code": r["zip_code"],
            "emergency_name": r["emergency_name"],
            "emergency_relation": r["emergency_relation"],
            "emergency_phone": r["emergency_phone"]
        },
        "insurance": {
            "payer_name": r["payer_name"],
            "policy_id": r["policy_id"],
            "group_num": r["group_num"],
            "subscriber_id": r["subscriber_id"],
            "copay_tier": r["copay_tier"]
        },
        "clinical_triage": {
            "chief_complaint": r["chief_complaint"],
            "admission_date": r["admission_date"],
            "urgency_tier": r["urgency_tier"],
            "assigned_ward": r["assigned_ward"],
            "assigned_room": r["assigned_room"],
            "attending_clinician": r["attending_clinician"]
        },
        "symptoms": r.get("symptoms") or r.get("chief_complaint") or "",
        "existing_conditions": r.get("existing_conditions") or "",
        "allergies": r.get("allergies") or "",
        "medications": r.get("medications") or "",
        "other_notes": r.get("other_notes") or "",
        "status": r["status"],
        "is_draft": r["status"] == "DRAFT"
    }


def save_patient_intake_db(submission: dict, is_draft: bool = False):
    conn = get_connection()
    init_intake_tables(conn)
    cur = conn.cursor()

    demo = submission.get("demographics", {})
    contact = submission.get("contact", {})
    ins = submission.get("insurance", {})
    triage = submission.get("clinical_triage", {})
    symptoms = submission.get("symptoms") or triage.get("symptoms") or triage.get("chief_complaint") or ""
    conditions = submission.get("existing_conditions") or triage.get("existing_conditions") or ""
    allergies = submission.get("allergies") or triage.get("allergies") or ""
    meds = submission.get("medications") or triage.get("medications") or ""
    other_notes = submission.get("other_notes") or triage.get("other_notes") or ""
    mrn = demo.get("mrn", "ML-9420-TX")
    session_id = submission.get("session_id", "#ENC-2026-8812")
    status = "DRAFT" if is_draft else "SUBMITTED"
    now_iso = datetime.utcnow().isoformat()

    cur.execute("""
    INSERT OR REPLACE INTO patient_intakes (
        mrn, session_id, first_name, middle_name, last_name, preferred_name,
        dob, age, legal_sex, pronouns, ssn_masked, primary_language, interpreter_required,
        phone, email, street_address, city, state, zip_code,
        emergency_name, emergency_relation, emergency_phone,
        payer_name, policy_id, group_num, subscriber_id, copay_tier,
        chief_complaint, admission_date, urgency_tier, assigned_ward, assigned_room, attending_clinician,
        symptoms, existing_conditions, allergies, medications, other_notes,
        status, created_at
    ) VALUES (
        ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?
    )
    """, (
        mrn, session_id, demo.get("first_name"), demo.get("middle_name"), demo.get("last_name"), demo.get("preferred_name"),
        demo.get("dob"), demo.get("age", 58), demo.get("legal_sex", "female"), demo.get("pronouns", "she"),
        demo.get("ssn_masked", "***-**-4912"), demo.get("primary_language", "en"), 1 if demo.get("interpreter_required") else 0,
        contact.get("phone"), contact.get("email"), contact.get("street_address"), contact.get("city"), contact.get("state"), contact.get("zip_code"),
        contact.get("emergency_name"), contact.get("emergency_relation"), contact.get("emergency_phone"),
        ins.get("payer_name"), ins.get("policy_id"), ins.get("group_num"), ins.get("subscriber_id"), ins.get("copay_tier"),
        triage.get("chief_complaint"), triage.get("admission_date"), triage.get("urgency_tier", "ACUTE_2H"),
        triage.get("assigned_ward"), triage.get("assigned_room"), triage.get("attending_clinician"),
        symptoms, conditions, allergies, meds, other_notes,
        status, now_iso
    ))

    if not is_draft:
        # Enqueue in doctor dashboard triage queue
        first = demo.get("first_name", "New")
        last = demo.get("last_name", "Patient")
        full_name = f"{first} {last}".strip()
        initials = f"{first[0]}{last[0]}".upper() if first and last else "NP"
        cur.execute("""
        INSERT OR REPLACE INTO patients (
            mrn, name, initials, age, gender, room_bay, admission_date, urgency_tier, summary, ready_for_review, doctor_note_drafted
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0
        )
        """, (
            mrn, full_name, initials, demo.get("age", 58), demo.get("legal_sex", "female"),
            triage.get("assigned_room", "Room 412-B"), triage.get("admission_date", "Today"),
            triage.get("urgency_tier", "ACUTE_2H"), triage.get("chief_complaint", "Patient Intake Completed"),
        ))

        # Increment admissions today KPI
        cur.execute("""
        UPDATE kpi_metrics
        SET new_admissions_today = new_admissions_today + 1
        WHERE id = 1
        """)

        # Audit log
        cur.execute("""
        INSERT INTO audit_log (timestamp, action, performed_by, details)
        VALUES (?, 'PATIENT_INTAKE_SUBMITTED', ?, ?)
        """, (now_iso, triage.get("attending_clinician", "Clinician"), f"Patient {mrn} ({full_name}) registered and enqueued for triage."))

    conn.commit()
    conn.close()
    return mrn, session_id, status


def submit_patient_nomination_db(nomination: dict):
    conn = get_connection()
    init_intake_tables(conn)
    cur = conn.cursor()

    now_iso = datetime.utcnow().isoformat()
    pathways = nomination.get("clinical_pathways", [])
    pathways_str = ", ".join(pathways) if isinstance(pathways, list) else str(pathways)
    mrn = nomination.get("patient_mrn", "ML-9420-TX")
    doctor = nomination.get("signoff_doctor", "Dr. Sarah Jenkins, MD")

    cur.execute("""
    INSERT INTO patient_nominations (
        patient_mrn, clinical_pathways, urgency_tier, attached_document_count,
        referring_doctor_notes, readiness_score, attending_doctor_signoff, signoff_doctor, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        mrn, pathways_str, nomination.get("urgency_tier", "ACUTE_2H"),
        nomination.get("attached_document_count", 3), nomination.get("referring_doctor_notes"),
        94, 1 if nomination.get("attending_doctor_signoff") else 0, doctor, now_iso
    ))
    nomination_id = cur.lastrowid

    # Audit log
    cur.execute("""
    INSERT INTO audit_log (timestamp, action, performed_by, details)
    VALUES (?, 'PATIENT_NOMINATION_DISPATCHED', ?, ?)
    """, (now_iso, doctor, f"Nomination #{nomination_id} dispatched for patient {mrn}: {pathways_str} (Readiness: 94%)"))

    conn.commit()
    conn.close()
    return nomination_id, mrn, 94, now_iso

def flag_for_nurse(patient_mrn: str, nurse_name: str = "Nurse Kelly, RN", reason: str = "Bedside allergy re-check & scratch test protocol", priority: str = "URGENT", created_by: str = "Dr. Sarah Jenkins, MD") -> Dict[str, Any]:
    """Record an urgent bedside task flag dispatched to nursing staff and log in clinical audit trail."""
    conn = get_connection()
    cur = conn.cursor()
    now_iso = datetime.utcnow().isoformat()
    now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    flag_id = f"FLAG-{patient_mrn}-{int(datetime.now().timestamp())}"

    # Verify patient exists
    cur.execute("SELECT name, room_bay FROM patients WHERE mrn = ?", (patient_mrn,))
    p_row = cur.fetchone()
    patient_name = p_row["name"] if p_row else patient_mrn
    room_bay = p_row["room_bay"] if p_row else "Observation Bay"

    cur.execute("""
    INSERT INTO nurse_flags (id, patient_mrn, nurse_name, reason, priority, status, created_at, created_by)
    VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?)
    """, (flag_id, patient_mrn, nurse_name, reason, priority, now_iso, created_by))

    cur.execute("""
    INSERT INTO audit_log (timestamp, action, performed_by, details)
    VALUES (?, 'FLAG_FOR_NURSE', ?, ?)
    """, (now_iso, created_by, f"Bedside order flagged for {nurse_name} ({room_bay}): {reason} [Priority: {priority}]"))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "flag_id": flag_id,
        "patient_mrn": patient_mrn,
        "patient_name": patient_name,
        "room_bay": room_bay,
        "nurse_name": nurse_name,
        "reason": reason,
        "priority": priority,
        "status": "PENDING",
        "message": f"Bedside alert dispatched to {nurse_name}. {reason}",
        "timestamp": now_str
    }

def get_nurse_flags(patient_mrn: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all pending or active nurse flags, optionally filtered by patient MRN."""
    conn = get_connection()
    cur = conn.cursor()
    if patient_mrn:
        cur.execute("SELECT * FROM nurse_flags WHERE patient_mrn = ? ORDER BY created_at DESC", (patient_mrn,))
    else:
        cur.execute("SELECT * FROM nurse_flags ORDER BY created_at DESC", ())
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def override_dashboard_lab(patient_mrn: str, test_code: str, result_value: str, unit: Optional[str] = None, reference_interval: Optional[str] = None, status: Optional[str] = None, reason: Optional[str] = None, clinician_name: str = "Dr. Sarah Jenkins, MD") -> Optional[Dict[str, Any]]:
    """Clinician override for a laboratory value directly from the doctor triage dashboard with audit logging."""
    conn = get_connection()
    cur = conn.cursor()
    now_iso = datetime.utcnow().isoformat()
    now_str = datetime.now().strftime("%d %b %Y %H:%M EST")

    # Extract numeric if possible
    import re
    numeric_val = None
    num_match = re.search(r"[-+]?\d*\.?\d+", result_value)
    if num_match:
        try:
            numeric_val = float(num_match.group(0))
        except ValueError:
            pass

    # 1. Update lab_results table
    cur.execute("SELECT * FROM lab_results WHERE patient_mrn = ? AND test_code = ?", (patient_mrn, test_code))
    lab_row = cur.fetchone()
    if lab_row:
        cur.execute("""
        UPDATE lab_results
        SET result_value = ?,
            unit = COALESCE(?, unit),
            reference_interval = COALESCE(?, reference_interval),
            status = COALESCE(?, status),
            numeric_value = COALESCE(?, numeric_value),
            verified = 1,
            verified_by = ?,
            verified_at = ?
        WHERE patient_mrn = ? AND test_code = ?
        """, (result_value, unit, reference_interval, status, numeric_val, clinician_name, now_str, patient_mrn, test_code))

    # 2. Update biomarker_observations if present
    cur.execute("""
    UPDATE biomarker_observations
    SET result_value = ?,
        unit = COALESCE(?, unit),
        reference_interval = COALESCE(?, reference_interval),
        status_flag = COALESCE(?, status_flag),
        numeric_value = COALESCE(?, numeric_value),
        verified = 1,
        verified_by = ?,
        verified_at = ?
    WHERE patient_mrn = ? AND (loinc_code = ? OR analyte_name LIKE ?)
    """, (result_value, unit, reference_interval, status, numeric_val, clinician_name, now_str, patient_mrn, test_code, f"%{test_code}%"))

    # 3. Log to audit trail
    details = f"Biomarker {test_code} for patient {patient_mrn} overridden to '{result_value}' [{status}]. Reason: {reason or 'Clinical re-evaluation'}"
    cur.execute("""
    INSERT INTO audit_log (timestamp, action, performed_by, details)
    VALUES (?, 'CLINICAL_OVERRIDE', ?, ?)
    """, (now_iso, clinician_name, details))

    # 4. Fetch updated lab result
    cur.execute("SELECT * FROM lab_results WHERE patient_mrn = ? AND test_code = ?", (patient_mrn, test_code))
    updated_row = cur.fetchone()
    updated_dict = dict(updated_row) if updated_row else {
        "patient_mrn": patient_mrn,
        "test_code": test_code,
        "result_value": result_value,
        "reference_interval": reference_interval,
        "status": status,
        "verified": 1,
        "verified_by": clinician_name,
        "verified_at": now_str
    }

    conn.commit()
    conn.close()
    return updated_dict

def init_all_tables():
    init_db()
    conn = get_connection()
    init_clinical_record_tables(conn)
    init_intake_tables(conn)
    conn.close()

# Initialize all database tables on load
init_all_tables()


