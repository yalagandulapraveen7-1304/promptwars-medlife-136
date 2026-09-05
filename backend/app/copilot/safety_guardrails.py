import re
from typing import Dict, Any, Tuple, Optional
from app.models.copilot import SafetyCheckResponse

PROHIBITED_INTENTS = [
    {
        "intent": "prescribing",
        "keywords": ["prescribe", "prescription", "what medication should i prescribe", "what drug to give", "which medication to start", "order antibiotic"],
        "regex": r"\b(prescribe|give medication|order (drug|antibiotic|medication)|which drug to give)\b"
    },
    {
        "intent": "dosage_change",
        "keywords": ["change the patient's dosage", "change dosage", "modify dose", "increase dose", "decrease dose", "titrate dosage", "adjust dose"],
        "regex": r"\b(change (the )?(patient'?s )?dosage|modify dose|adjust dose|titrate|increase dose|decrease dose)\b"
    },
    {
        "intent": "definitive_diagnosis",
        "keywords": ["diagnose the patient", "diagnose", "definitely have diabetes", "confirm diagnosis", "what is the diagnosis"],
        "regex": r"\b(diagnose( the patient)?|definitely have|confirm (the )?diagnosis|does (the )?patient definitely have)\b"
    },
    {
        "intent": "treatment_recommendation",
        "keywords": ["what treatment should the patient receive", "what treatment to order", "recommend treatment", "therapeutic course"],
        "regex": r"\b(what treatment should|recommend treatment|determine therapy|therapeutic regimen to order)\b"
    }
]

SAFE_PROVENANCE_PATTERNS = [
    r"show( the)? source",
    r"provenance",
    r"where did this come from",
    r"which document",
    r"citation",
    r"bounding box"
]

SAFE_REDIRECT_DISCLAIMER = (
    "MedLens Clinical Safety Protocol [Rule SAFE-00006 to SAFE-00010]: "
    "MedLens AI Copilot is strictly restricted to summarizing documented clinical information only. "
    "Autonomous diagnostic conclusions, drug prescribing, and dosage modifications are prohibited. "
    "Please consult the licensed attending physician for patient-specific diagnostic evaluations and prescription orders."
)

CLINICAL_KEYWORDS = {
    # Medical personnel, facilities & workflows
    "doctor", "dr", "dr.", "physician", "attending", "nurse", "rn", "clinician",
    "provider", "specialist", "medical", "clinic", "hospital", "ward", "icu", "er",
    "ambulatory", "inpatient", "outpatient", "emergency", "cardiology", "oncology",
    "hematology", "pediatric", "radiology", "pathology", "surgery", "surgical",
    "bedside", "census", "roster", "intake", "discharge", "admit", "admission",
    "referral", "nomination", "triage", "bed", "vitals", "provenance", "citation",
    "audit", "ledger", "sign-off", "verified", "unverified", "discrepancy", "conflict",
    "contradiction", "ocr", "extraction", "specimen", "sample", "protocol", "care",
    
    # EHR & Data
    "patient", "mrn", "chart", "record", "ehr", "emr", "epic", "cerner", "fhir",
    "hipaa", "demographic", "history", "assessment", "plan", "soap", "baseline",
    "missing", "incomplete", "summary", "summarize", "report", "reports", "compare",
    "comparison", "trend", "delta", "status", "profile", "registry", "value",
    
    # Laboratory & Analytes
    "lab", "labs", "laboratory", "panel", "test", "tests", "biomarker", "biomarkers",
    "analyte", "analytes", "blood", "urine", "serum", "plasma", "cbc", "bmp", "cmp",
    "lft", "lipid", "hgb", "hemoglobin", "hematocrit", "hct", "wbc", "rbc",
    "platelet", "platelets", "mcv", "mch", "mchc", "rdw", "ferritin", "iron",
    "tibc", "creatinine", "bun", "urea", "glucose", "a1c", "hba1c", "potassium",
    "sodium", "chloride", "bicarbonate", "co2", "calcium", "magnesium", "phosphorus",
    "troponin", "ast", "alt", "alp", "bilirubin", "albumin", "protein", "crp",
    "esr", "inr", "pt", "ptt", "cholesterol", "triglyceride", "ldl", "hdl", "gfr",
    "egfr", "range", "reference", "interval", "abnormal", "low", "high", "critical",
    "normal", "out-of-range", "outside", "elevated", "depressed", "deficiency",
    
    # Medications & Pharmacology
    "medication", "medications", "med", "meds", "medicine", "medicines", "drug",
    "drugs", "rx", "prescription", "prescriptions", "prescribe", "dose", "dosage",
    "dosing", "pill", "pills", "tablet", "tablets", "capsule", "capsules", "mg",
    "mcg", "g", "ml", "unit", "units", "antibiotic", "antibiotics", "penicillin",
    "amoxicillin", "ampicillin", "cephalosporin", "ciprofloxacin", "metformin",
    "lisinopril", "atorvastatin", "amlodipine", "aspirin", "heparin", "warfarin",
    "insulin", "prednisone", "steroid", "steroids", "albuterol", "gabapentin",
    "allergy", "allergies", "allergic", "anaphylaxis", "contraindication",
    "contraindications", "interaction", "interactions", "side-effect", "adverse",
    "nkda", "infusion", "iv", "injection",
    
    # Conditions, Symptoms & Anatomy
    "symptom", "symptoms", "condition", "conditions", "diagnosis", "diagnoses",
    "diagnose", "diagnostic", "disease", "diseases", "disorder", "disorders",
    "illness", "infection", "infections", "pain", "fever", "cough", "fatigue",
    "dyspnea", "breath", "breathing", "nausea", "vomiting", "diarrhea", "headache",
    "dizziness", "edema", "swelling", "rash", "hypertension", "hypotension",
    "diabetes", "anemia", "anemic", "microcytic", "macrocytic", "cardiac", "heart",
    "pulmonary", "lung", "lungs", "renal", "kidney", "kidneys", "hepatic", "liver",
    "gastrointestinal", "gi", "neurological", "brain", "stroke", "seizure",
    "cancer", "tumor", "biopsy", "organ", "vital", "vitals", "bp", "pressure",
    "pulse", "heartrate", "spo2", "temperature", "temp"
}

CLINICAL_REGEX = re.compile(
    r"\b("
    r"(pat|rep|ml|lc)-\d+|"
    r"mrn\s*#?\s*\w+|"
    r"elena|rostova|marcus|vance|arthur|pendleton|david|chen|priya|patel|eleanor|nikhil|kumar|"
    r"cbc|bmp|cmp|hgb|wbc|rbc|mcv|a1c|gfr|bun|pt|inr|"
    r"\d+(\.\d+)?\s*(g/dl|mg/dl|mmol/l|meq/l|mcg/l|ug/dl|u/l|ng/ml|%|bpm|mmhg)|"
    r"out\s*of\s*range|reference\s*range|blood\s*pressure|heart\s*rate|drug\s*allergy|"
    r"clinical\s*(note|summary|record|decision|guidance|status)|"
    r"safe(ty)?\s*(guardrail|redirect|hold)|"
    r"sign[- ]?off|triage\s*queue"
    r")\b",
    re.IGNORECASE
)

NON_CLINICAL_INDICATORS = [
    r"\b(capital of|weather in|who won|football|soccer|cricket|basketball|tennis|nfl|nba|world cup|olympics)\b",
    r"\b(recipe|bake|cook|cake|pizza|pasta|cookie|ingredients|restaurant|food)\b",
    r"\b(write\s+(a\s+)?(python|javascript|code|script|html|css|sql|function|program|loop|class))\b",
    r"\b(joke|funny|riddle|poem|poetry|song|lyrics|movie|actor|actress|hollywood|music)\b",
    r"\b(stock|stocks|crypto|bitcoin|invest|investing|trading|forex|dividend|mortgage|finance|money)\b",
    r"\b(president|election|senate|politics|prime minister|parliament|governor|vote|campaign)\b",
    r"\b(car|repair|engine|tire|vehicle|dealership|mechanic|flight|travel|hotel|airline)\b",
    r"\b(game|playstation|xbox|nintendo|minecraft|fortnite|gaming)\b"
]

EMPTY_INPUT_GUIDE = (
    "[Input Required]: Please enter a specific clinical question or patient inquiry.\n\n"
    "Valid Medical Input Examples:\n"
    "• \"Summarize out-of-range lab results for today's clinic\"\n"
    "• \"Audit allergy discrepancies across active roster\"\n"
    "• \"Check Elena Rostova CBC hemoglobin trend\"\n"
    "• \"Show document provenance for LabCorp specimen #LC-9011\""
)

def format_out_of_domain_response(query: str) -> str:
    cleaned = query.strip()
    return (
        f"[MedLens Clinical Domain Guardrail]: The inquiry \"{cleaned}\" is not related to a doctor, patient, clinical record, laboratory test, or medical field.\n\n"
        "MedLens AI Copilot is a specialized clinical workstation intelligence assistant designed exclusively for physicians, nurses, and healthcare providers to review verified patient records, analyze laboratory results, and audit clinical documentation.\n\n"
        "Valid Medical Inputs According to Clinical Workflows:\n\n"
        "1. Laboratory & Biomarker Analysis:\n"
        "   • \"Summarize out-of-range lab results for Elena Rostova (ML-8841)\"\n"
        "   • \"What is the reference range and documented value for Hemoglobin / Ferritin?\"\n"
        "   • \"Which latest laboratory results are outside the report-provided reference ranges?\"\n\n"
        "2. Cross-Document Allergy & Contradiction Detection:\n"
        "   • \"Audit allergy discrepancies between digital intake and historical EHR records\"\n"
        "   • \"Check Marcus Vance (ML-7920) for Penicillin allergy contraindications\"\n\n"
        "3. Longitudinal Trend & Specimen Comparisons:\n"
        "   • \"Compare the latest reports for this patient and show analyte deltas\"\n"
        "   • \"What is the trend for Serum Creatinine across consecutive specimens?\"\n\n"
        "4. Provenance & Traceable Citations:\n"
        "   • \"Show the source and provenance of this laboratory value\"\n"
        "   • \"Verify OCR table extraction confidence for Vance_Metabolic.pdf\"\n\n"
        "5. Clinical Operations & Triage Queue:\n"
        "   • \"Show active roster triage priority and pending clinician sign-offs\"\n"
        "   • \"Audit patient intake completeness for Sections A through H\""
    )

def is_clinical_query(query: str) -> bool:
    """
    Determines whether a query pertains to the medical/clinical domain.
    """
    q_norm = query.strip().lower()
    if not q_norm:
        return False
        
    # Check explicit non-clinical indicators
    for pat in NON_CLINICAL_INDICATORS:
        if re.search(pat, q_norm, re.IGNORECASE):
            return False

    # Check regex patterns (IDs, measurements, medical terms)
    if CLINICAL_REGEX.search(q_norm):
        return True
        
    # Check keyword tokens
    words = re.findall(r"\b[a-z\.\-\#]+\b", q_norm)
    if any(w in CLINICAL_KEYWORDS for w in words):
        return True

    return False

class SafetyGuardrailEngine:
    """
    Implements the 15 MedLens Safety Rules from the synthetic clinical dataset.
    Ensures Copilot acts as a source-grounded assistant that summarizes verified records,
    strictly intercepting diagnostic and prescribing prompts with safe_redirect,
    and directing non-clinical inputs to valid medical query guidance.
    """

    def __init__(self, safety_examples: Optional[list] = None):
        self.safety_examples = safety_examples or []

    def evaluate_query(self, query: str) -> Dict[str, Any]:
        """
        Classifies query into:
        1. 'out_of_domain' (Empty or not related to doctor/medical field -> shows valid inputs)
        2. 'safe_redirect' (Prohibited: diagnosis, prescription, dosage adjustments)
        3. 'show_provenance' (Permitted: document and provenance lookups)
        4. 'safe_answer_from_record' (Permitted: factual lab, symptom, and history queries)
        """
        q_clean = query.strip()
        q_norm = q_clean.lower()

        # 0. Empty or whitespace check
        if not q_clean or len(q_clean) < 2:
            return {
                "is_safe": False,
                "action": "out_of_domain",
                "rule_id": "RULE-EMPTY-INPUT",
                "rule_text": "A valid clinical query is required.",
                "redirect_message": EMPTY_INPUT_GUIDE
            }

        # 1. Exact match check against dataset safety examples
        for ex in self.safety_examples:
            if ex.get("question", "").strip().lower() == q_norm:
                action = ex.get("expected_action", "safe_answer_from_record")
                is_safe = (action != "safe_redirect")
                return {
                    "is_safe": is_safe,
                    "action": action,
                    "rule_id": ex.get("id"),
                    "rule_text": ex.get("rule", "Summarize documented information only; do not diagnose, prescribe, or change treatment."),
                    "redirect_message": SAFE_REDIRECT_DISCLAIMER if not is_safe else None
                }

        # 2. Check for prohibited diagnostic / prescribing / dosage intents
        for intent_def in PROHIBITED_INTENTS:
            # Check keywords
            if any(kw in q_norm for kw in intent_def["keywords"]):
                return {
                    "is_safe": False,
                    "action": "safe_redirect",
                    "rule_id": f"RULE-{intent_def['intent'].upper()}",
                    "rule_text": "Summarize documented information only; do not diagnose, prescribe, or change treatment.",
                    "redirect_message": SAFE_REDIRECT_DISCLAIMER
                }
            # Check regex
            if re.search(intent_def["regex"], q_norm, re.IGNORECASE):
                return {
                    "is_safe": False,
                    "action": "safe_redirect",
                    "rule_id": f"RULE-{intent_def['intent'].upper()}",
                    "rule_text": "Summarize documented information only; do not diagnose, prescribe, or change treatment.",
                    "redirect_message": SAFE_REDIRECT_DISCLAIMER
                }

        # 3. Check for provenance inquiry
        if any(re.search(pat, q_norm, re.IGNORECASE) for pat in SAFE_PROVENANCE_PATTERNS):
            return {
                "is_safe": True,
                "action": "show_provenance",
                "rule_id": "SAFE-PROVENANCE",
                "rule_text": "Show exact document, line, and field provenance attribution.",
                "redirect_message": None
            }

        # 4. Domain boundary check (Must be related to doctor, patient, or medical field)
        if not is_clinical_query(q_clean):
            return {
                "is_safe": False,
                "action": "out_of_domain",
                "rule_id": "RULE-DOMAIN-SCOPE",
                "rule_text": "MedLens AI Copilot is restricted strictly to healthcare, clinical EHR data, laboratory analysis, and medical workflows.",
                "redirect_message": format_out_of_domain_response(query)
            }

        # 5. Default safe record extraction
        return {
            "is_safe": True,
            "action": "safe_answer_from_record",
            "rule_id": "SAFE-RECORD-LOOKUP",
            "rule_text": "Summarize documented information only; do not diagnose, prescribe, or change treatment.",
            "redirect_message": None
        }

def check_safety(query: str, safety_examples: Optional[list] = None) -> SafetyCheckResponse:
    engine = SafetyGuardrailEngine(safety_examples)
    res = engine.evaluate_query(query)
    return SafetyCheckResponse(
        query=query,
        is_safe=res["is_safe"],
        expected_action=res["action"],
        rule_id=res["rule_id"],
        rule_text=res["rule_text"],
        safe_redirect_message=res["redirect_message"]
    )
