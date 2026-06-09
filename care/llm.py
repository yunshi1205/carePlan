from django.conf import settings
from anthropic import Anthropic

from care.debug_flow import flow, flow_break


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

    flow_break(
        "L1",
        "llm.generate_care_plan — calling Anthropic",
        model=settings.ANTHROPIC_MODEL,
        patient=f"{patient_first_name} {patient_last_name}",
        medication=medication_name,
    )

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
    text = blocks[0].text if blocks else ""
    flow(
        "L2",
        "llm.generate_care_plan — Anthropic returned",
        response_chars=len(text),
    )
    return text
