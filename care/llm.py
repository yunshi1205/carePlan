from django.conf import settings
from anthropic import Anthropic


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
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    user_content = f"""Patient: {patient_first_name} {patient_last_name}
Medication: {medication_name}
Primary diagnosis: {primary_diagnosis or "Not specified"}

Patient records:
{patient_records}
"""

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        temperature=0.3,
    )
    blocks = message.content
    if not blocks:
        return ""
    return blocks[0].text
