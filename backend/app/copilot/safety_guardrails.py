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

class SafetyGuardrailEngine:
    """
    Implements the 15 MedLens Safety Rules from the synthetic clinical dataset.
    Ensures Copilot acts as a source-grounded assistant that summarizes verified records,
    strictly intercepting diagnostic and prescribing prompts with safe_redirect.
    """

    def __init__(self, safety_examples: Optional[list] = None):
        self.safety_examples = safety_examples or []

    def evaluate_query(self, query: str) -> Dict[str, Any]:
        """
        Classifies query into:
        1. 'safe_redirect' (Prohibited: diagnosis, prescription, dosage adjustments)
        2. 'show_provenance' (Permitted: document and provenance lookups)
        3. 'safe_answer_from_record' (Permitted: factual lab, symptom, and history queries)
        """
        q_norm = query.strip().lower()

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

        # 4. Default safe record extraction
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
