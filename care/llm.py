from django.conf import settings
from openai import OpenAI


SYSTEM_PROMPT = """You are a clinical pharmacist writing a specialty pharmacy care plan.
Output plain text with exactly these four sections and headings:

Problem list / Drug therapy problems (DTPs)
Goals (SMART)
Pharmacist interventions / plan
Monitoring plan & lab schedule

Be concise and clinically plausible based only on the input provided."""


def generate_care_plan(
    *,
    patient_first_name: str,
    patient_last_name: str,
    medication_name: str,
    primary_diagnosis: str,
    patient_records: str,
) -> str:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    user_content = f"""Patient: {patient_first_name} {patient_last_name}
Medication: {medication_name}
Primary diagnosis: {primary_diagnosis or "Not specified"}

Patient records:
{patient_records}
"""

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content or ""
