"""
MedLens Clinical AI Copilot Engine
Grounded in MedLens Synthetic Dataset v1 & Zero-Hallucination Clinical Rules.
"""
from app.copilot.knowledge_base import KnowledgeBase, get_knowledge_base
from app.copilot.safety_guardrails import SafetyGuardrailEngine, check_safety
from app.copilot.conflict_detector import ConflictDetector, detect_conflicts_for_patient
from app.copilot.engine import CopilotEngine, get_copilot_engine
from app.copilot.evaluation_harness import GoldenEvaluationHarness
