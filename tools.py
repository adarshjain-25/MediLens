"""
The two required tools for the track, both deterministic Python (no LLM inside):

1. simplify_and_flag_results  -- parses lab values out of the report text and checks
   each one against a reference-range table. Runs the instant a document is ingested.
2. find_specialist             -- looks up which specialist a flagged condition maps to.

An LLM (Groq) is used ONLY afterwards, to turn the deterministic findings into a
plain-language sentence -- it never decides what counts as abnormal.
"""
import re

from llm import chat

# ---- 1. Reference ranges (deterministic) ---------------------------------
# (aliases to search for, low, high, unit, human label)
REFERENCE_RANGES = [
    (["glucose", "fasting glucose", "blood sugar"], 70, 99, "mg/dL", "blood sugar"),
    (["hemoglobin", "hgb", "hb"], 12.0, 16.5, "g/dL", "hemoglobin"),
    (["hba1c", "a1c"], 4.0, 5.6, "%", "hba1c"),
    (["total cholesterol", "cholesterol"], 0, 200, "mg/dL", "total cholesterol"),
    (["ldl", "ldl cholesterol"], 0, 100, "mg/dL", "ldl cholesterol"),
    (["hdl", "hdl cholesterol"], 40, 200, "mg/dL", "hdl cholesterol"),
    (["triglycerides"], 0, 150, "mg/dL", "triglycerides"),
    (["tsh"], 0.4, 4.0, "uIU/mL", "tsh"),
    (["alt", "sgpt"], 7, 56, "U/L", "alt (liver enzyme)"),
    (["ast", "sgot"], 8, 48, "U/L", "ast (liver enzyme)"),
    (["creatinine"], 0.6, 1.3, "mg/dL", "creatinine"),
    (["wbc", "white blood cell"], 4.5, 11.0, "x10^3/uL", "white blood cell count"),
    (["platelet", "platelets"], 150, 450, "x10^3/uL", "platelet count"),
    (["systolic"], 90, 120, "mmHg", "systolic blood pressure"),
    (["diastolic"], 60, 80, "mmHg", "diastolic blood pressure"),
]

_NUM = r"[:\s\-]{0,6}([\d]+\.?[\d]*)"


def _find_value(text: str, aliases: list[str]):
    for alias in sorted(aliases, key=len, reverse=True):
        m = re.search(re.escape(alias) + _NUM, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                continue
    return None


def simplify_and_flag_results(medical_text: str) -> dict:
    """Deterministically scans the report for known lab values and checks each
    against its reference range. Returns which are flagged (out of range) and
    which are normal, plus a short plain-language summary written by the LLM
    from those findings (the LLM never decides the flags themselves)."""
    findings, flags, normal, details = [], [], [], {}

    for aliases, low, high, unit, label in REFERENCE_RANGES:
        value = _find_value(medical_text, aliases)
        if value is None:
            continue
        if value < low:
            status = "low"
            flags.append(label)
            findings.append(f"{label}: {value} {unit} (low; normal {low}-{high})")
        elif value > high:
            status = "high"
            flags.append(label)
            findings.append(f"{label}: {value} {unit} (high; normal {low}-{high})")
        else:
            status = "normal"
            normal.append(label)
            findings.append(f"{label}: {value} {unit} (normal; range {low}-{high})")
        details[label] = {"value": value, "unit": unit, "low": low, "high": high, "status": status}

    if not findings:
        return {
            "summary": "No recognized lab values could be matched in this document, "
                       "so no automatic flags were generated. You can still ask questions below.",
            "flags": [],
            "normal": [],
            "details": {},
        }

    prompt = (
        "Rewrite these lab findings as one short, plain-language sentence a "
        "non-medical patient can understand. Do not add any values not listed. "
        "Findings:\n" + "\n".join(findings)
    )
    try:
        summary = chat(prompt, temperature=0.2).strip()
    except Exception:
        summary = f"{len(flags)} value(s) outside the normal range, {len(normal)} within range."

    return {"summary": summary, "flags": flags, "normal": normal, "details": details}


# ---- 2. Specialist lookup (deterministic) ---------------------------------
SPECIALIST_MAP = {
    "blood sugar": "Endocrinologist",
    "hba1c": "Endocrinologist",
    "total cholesterol": "Cardiologist",
    "ldl cholesterol": "Cardiologist",
    "hdl cholesterol": "Cardiologist",
    "triglycerides": "Cardiologist",
    "hemoglobin": "Hematologist",
    "white blood cell count": "Hematologist",
    "platelet count": "Hematologist",
    "tsh": "Endocrinologist",
    "alt (liver enzyme)": "Hepatologist / Gastroenterologist",
    "ast (liver enzyme)": "Hepatologist / Gastroenterologist",
    "creatinine": "Nephrologist",
    "systolic blood pressure": "Cardiologist",
    "diastolic blood pressure": "Cardiologist",
}


def find_specialist(flagged_conditions_str: str) -> dict:
    """Takes a comma-separated string of flagged conditions and returns, for
    each, the specialist to see, via a fixed lookup table (no LLM)."""
    conditions = [c.strip().lower() for c in flagged_conditions_str.split(",") if c.strip()]
    return {c: SPECIALIST_MAP.get(c, "General Practitioner (consult for referral)") for c in conditions}


# ---- Severity (deterministic, no LLM) -------------------------------------
def severity(value: float, low: float, high: float, status: str):
    """Returns (level_label, urgency_label, priority_tier, pct_out_of_range) -- pure math, no LLM.
    priority_tier is one of "normal", "followup", "high" -- used for the three summary counters."""
    if status == "normal":
        return "Within configured reference range", "No action needed", "normal", 0.0
    pct = ((value - high) / high * 100) if status == "high" and high else \
          ((low - value) / low * 100) if status == "low" and low else 0.0
    pct = round(max(pct, 0.0), 1)
    direction = "Above" if status == "high" else "Below"
    if pct < 10:
        level, urgency, tier = f"{direction} configured reference range (mild)", "Routine follow-up recommended", "followup"
    elif pct < 30:
        level, urgency, tier = f"{direction} configured reference range (moderate)", "Follow-up recommended", "followup"
    else:
        level, urgency, tier = f"{direction} configured reference range (significant)", "Prompt discussion recommended", "high"
    return level, urgency, tier, pct


DETECTION_METHOD = "Rule-based reference-range comparison"

# Deterministic "why this specialty" -- paired with SPECIALIST_MAP, no LLM.
SPECIALTY_REASONS = {
    "Endocrinologist": "Endocrinologists manage hormones and metabolism, including blood sugar and thyroid regulation.",
    "Cardiologist": "Cardiologists assess cardiovascular risk factors such as cholesterol, triglycerides and blood pressure.",
    "Hematologist": "Hematologists specialize in blood cell counts and blood-related conditions.",
    "Hepatologist / Gastroenterologist": "These specialists evaluate liver function and enzyme levels.",
    "Nephrologist": "Nephrologists focus on kidney function markers such as creatinine.",
}


def discussion_questions(label: str) -> list[str]:
    """Fixed, deterministic list of questions a patient could ask -- not LLM-generated,
    so it never drifts into medical advice."""
    return [
        f"What could cause my {label} result to be outside the reference range?",
        "Should this test be repeated to confirm the result?",
        "Are there other results in this report that should be considered together with this one?",
        "Does my medical history change how this result should be interpreted?",
    ]


# ---- Lifestyle guidance (LLM phrasing of an already-fixed list of labels) --
_GUIDANCE_FALLBACK = {
    "definition": "A lab value measured in this report.",
    "limit": "See your reference range above.",
    "foods_to_eat": ["Ask your doctor for personalized dietary guidance."],
    "foods_to_avoid": ["Ask your doctor for personalized dietary guidance."],
    "advantages": "Keeping this value in range supports your overall health.",
    "disadvantages": "Leaving this value out of range unmanaged may affect your health over time.",
}


def generate_guidance(details: dict) -> dict:
    """One batched call: for every parsed lab value (flagged or normal), get a
    definition, target limit, foods to eat/avoid, and why it matters. The set of
    labels and their status was already fixed deterministically -- this only
    writes the explanatory text, it cannot change what was flagged."""
    if not details:
        return {}

    items = "\n".join(
        f"- {label}: value {d['value']} {d['unit']}, normal range {d['low']}-{d['high']}, status: {d['status']}"
        for label, d in details.items()
    )
    prompt = f"""
For each lab item below, write patient-friendly guidance. Respond ONLY with a JSON object
mapping each exact label (as given) to an object with these keys:
"definition" (1 sentence, what this test measures),
"limit" (1 short sentence stating the healthy target range or limit),
"foods_to_eat" (a list of 3-5 short food items that help keep it in range),
"foods_to_avoid" (a list of 3-5 short food items to limit or avoid),
"advantages" (1 sentence on the benefit of keeping it controlled),
"disadvantages" (1 sentence on the risk of leaving it uncontrolled).
Do not add a medical diagnosis. Keep every string short.

Lab items:
{items}
"""
    try:
        raw = chat(prompt, json_mode=True, temperature=0.3)
        import json
        parsed = json.loads(raw)
        return {label: {**_GUIDANCE_FALLBACK, **parsed.get(label, {})} for label in details}
    except Exception:
        return {label: dict(_GUIDANCE_FALLBACK) for label in details}
