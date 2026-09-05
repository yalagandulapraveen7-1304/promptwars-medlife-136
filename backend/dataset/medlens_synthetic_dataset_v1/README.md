# MedLens Synthetic Dataset v1

Synthetic/fictitious development dataset for the MedLens clinical-information intelligence prototype.
It is NOT real patient data and is NOT a source of medical truth.

Contents:
- 100 linked synthetic patients
- 300 synthetic laboratory reports
- 2,400 structured lab result rows
- 100 prescription records
- 100 clinical notes
- 300 medical-report extraction examples split into train/validation/test
- 400 doctor-copilot QA examples split into train/validation/test
- 20 controlled conflict examples
- 100 missing-information examples
- 15 safety examples split into train/validation/test
- provenance examples
- 100-patient golden evaluation set

Important:
1. Reference ranges in this dataset are explicitly marked as synthetic report-provided ranges.
2. The model must not infer medical reference ranges from this dataset.
3. Conflict examples require human verification.
4. Safety examples prohibit diagnosis, prescribing, and dosage changes.
5. Keep the final evaluation set isolated from training.
