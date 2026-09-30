"""Synthetic demo documents -- clearly labeled, never implied to be real patients."""

ROUTINE = """Complete Blood Count
Hemoglobin: 14.1 g/dL
White Blood Cell Count: 6.5 x10^3/uL
Platelet Count: 310 x10^3/uL

Lipid Panel
Total Cholesterol: 178 mg/dL
LDL Cholesterol: 92 mg/dL
HDL Cholesterol: 58 mg/dL
Triglycerides: 110 mg/dL

Metabolic Panel
Fasting Glucose: 88 mg/dL
Creatinine: 0.9 mg/dL

Clinical Notes
Routine annual check-up. Patient reports no symptoms. All results within expected ranges.
"""

MULTIPLE_FOLLOWUP = """Complete Blood Count
Hemoglobin: 10.8 g/dL
White Blood Cell Count: 7.2 x10^3/uL
Platelet Count: 260 x10^3/uL

Lipid Panel
Total Cholesterol: 235 mg/dL
LDL Cholesterol: 148 mg/dL
HDL Cholesterol: 44 mg/dL
Triglycerides: 190 mg/dL

Metabolic Panel
Fasting Glucose: 132 mg/dL
HbA1c: 7.8 %
Creatinine: 1.0 mg/dL

Thyroid Panel
TSH: 6.1 uIU/mL

Liver Function
ALT: 61 U/L
AST: 40 U/L

Vitals
Systolic: 128 mmHg
Diastolic: 82 mmHg

Clinical Notes
Patient reports occasional fatigue and mild headaches. No acute distress. Advised to
follow up on cholesterol, glucose and thyroid results and revisit in six weeks.
"""

DISCHARGE_SUMMARY = """Discharge Summary

Admission Reason: Chest discomfort, evaluated for cardiac cause.
Hospital Course: Patient monitored for 24 hours. Cardiac enzymes trended down.
ECG showed no acute changes on repeat testing.

Metabolic Panel
Fasting Glucose: 101 mg/dL
Creatinine: 0.8 mg/dL

Medications
- Aspirin 81mg once daily
- Atorvastatin 20mg at bedtime

Clinical Notes
Discharged in stable condition with outpatient cardiology follow-up scheduled.
Patient advised on activity restrictions for one week.
"""

PRESCRIPTION_EXAMPLE = """Prescription

Patient advised the following outpatient medications:
- Metformin 500mg twice daily with meals
- Lisinopril 10mg once daily in the morning
- Atorvastatin 20mg once daily at bedtime

Clinical Notes
Prescribed following routine follow-up for blood sugar and blood pressure management.
Recheck labs recommended in 3 months.
"""

DEMO_REPORTS = [
    {
        "id": "routine",
        "title": "Routine Lab Report",
        "description": "A standard annual panel with results mostly within reference range.",
        "text": ROUTINE,
    },
    {
        "id": "followup",
        "title": "Multiple Follow-up Findings",
        "description": "A panel with several values outside their configured reference ranges.",
        "text": MULTIPLE_FOLLOWUP,
    },
    {
        "id": "discharge",
        "title": "Discharge Summary",
        "description": "A hospital discharge note with limited numeric lab values.",
        "text": DISCHARGE_SUMMARY,
    },
    {
        "id": "prescription",
        "title": "Prescription Example",
        "description": "A medication list with no lab values -- demonstrates the empty-result state.",
        "text": PRESCRIPTION_EXAMPLE,
    },
]

# kept for backward compatibility with earlier code paths
SAMPLE_REPORT = MULTIPLE_FOLLOWUP
