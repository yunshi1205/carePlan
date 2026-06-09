from datetime import date

from django.core.management.base import BaseCommand

from care.models import CarePlan, Order, Patient, Provider

MOCK_CARE_PLAN = """Problem list / Drug therapy problems (DTPs)
- Need for rapid immunomodulation
- Risk of infusion-related reactions

Goals (SMART)
- Achieve clinically meaningful improvement within 2 weeks

Pharmacist interventions / plan
- Dosing & Administration
- Premedication

Monitoring plan & lab schedule
- Before first infusion: CBC, BMP, baseline vitals
"""


class Command(BaseCommand):
    help = "Load mock patients, providers, orders, and care plans for local dev"

    def handle(self, *args, **options):
        if Patient.objects.filter(mrn="000123").exists():
            self.stdout.write("Mock data already present — skipping.")
            return

        patients = [
            Patient.objects.create(
                first_name="A.",
                last_name="B.",
                mrn="000123",
                date_of_birth=date(1979, 6, 8),
            ),
            Patient.objects.create(
                first_name="Jane",
                last_name="Smith",
                mrn="000456",
                date_of_birth=date(1965, 3, 15),
            ),
            Patient.objects.create(
                first_name="Robert",
                last_name="Chen",
                mrn="000789",
                date_of_birth=date(1988, 11, 22),
            ),
            Patient.objects.create(
                first_name="Maria",
                last_name="Garcia",
                mrn="001012",
                date_of_birth=date(1972, 7, 4),
            ),
        ]

        providers = [
            Provider.objects.create(
                name="Dr. Sarah Neurology",
                npi="1234567890",
            ),
            Provider.objects.create(
                name="Dr. James Rheum",
                npi="9876543210",
            ),
        ]

        orders_spec = [
            {
                "patient": patients[0],
                "provider": providers[0],
                "medication_name": "IVIG",
                "primary_diagnosis": "Generalized myasthenia gravis (G70.00)",
                "additional_diagnoses": ["I10", "K21.9"],
                "medication_history": [
                    "Pyridostigmine 60 mg PO q6h",
                    "Prednisone 10 mg PO daily",
                ],
                "patient_records": "Progressive proximal muscle weakness over 2 weeks.",
                "care_status": CarePlan.STATUS_COMPLETED,
                "care_content": MOCK_CARE_PLAN,
            },
            {
                "patient": patients[1],
                "provider": providers[0],
                "medication_name": "Adalimumab",
                "primary_diagnosis": "Rheumatoid arthritis (M06.9)",
                "additional_diagnoses": ["E11.9"],
                "medication_history": ["Methotrexate 15 mg weekly"],
                "patient_records": "Joint pain and morning stiffness; starting biologic.",
                "care_status": CarePlan.STATUS_COMPLETED,
                "care_content": MOCK_CARE_PLAN.replace("immunomodulation", "disease control"),
            },
            {
                "patient": patients[2],
                "provider": providers[1],
                "medication_name": "Infliximab",
                "primary_diagnosis": "Crohn's disease (K50.90)",
                "additional_diagnoses": [],
                "medication_history": ["Mesalamine 2.4 g daily"],
                "patient_records": "Flare with abdominal pain; induction therapy planned.",
                "care_status": CarePlan.STATUS_PROCESSING,
                "care_content": None,
            },
            {
                "patient": patients[3],
                "provider": providers[1],
                "medication_name": "Eculizumab",
                "primary_diagnosis": "Paroxysmal nocturnal hemoglobinuria (D59.5)",
                "additional_diagnoses": ["D64.9"],
                "medication_history": ["Folic acid 1 mg daily"],
                "patient_records": "Fatigue and hemolysis labs; complement inhibitor initiated.",
                "care_status": CarePlan.STATUS_FAILED,
                "care_content": None,
                "care_error": "Mock failed generation for demo",
            },
            {
                "patient": patients[0],
                "provider": providers[0],
                "medication_name": "Rituximab",
                "primary_diagnosis": "Generalized myasthenia gravis (G70.00)",
                "additional_diagnoses": ["I10"],
                "medication_history": ["IVIG prior course"],
                "patient_records": "Second-line therapy after incomplete IVIG response.",
                "care_status": CarePlan.STATUS_PENDING,
                "care_content": None,
            },
        ]

        for spec in orders_spec:
            order = Order.objects.create(
                patient=spec["patient"],
                provider=spec["provider"],
                medication_name=spec["medication_name"],
                primary_diagnosis=spec["primary_diagnosis"],
                additional_diagnoses=spec["additional_diagnoses"],
                medication_history=spec["medication_history"],
                patient_records=spec["patient_records"],
            )
            CarePlan.objects.create(
                order=order,
                status=spec["care_status"],
                content=spec.get("care_content"),
                error=spec.get("care_error"),
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(patients)} patients, {len(providers)} providers, "
                f"{len(orders_spec)} orders with care plans."
            )
        )
