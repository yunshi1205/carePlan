import uuid

from django.db import models


class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    mrn = models.CharField(max_length=6, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "patient"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.mrn})"


class Provider(models.Model):
    name = models.CharField(max_length=200)
    npi = models.CharField(max_length=10, unique=True)

    class Meta:
        db_table = "provider"

    def __str__(self) -> str:
        return f"{self.name} ({self.npi})"


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="orders"
    )
    provider = models.ForeignKey(
        Provider, on_delete=models.PROTECT, related_name="orders"
    )
    medication_name = models.CharField(max_length=200)
    primary_diagnosis = models.CharField(max_length=500, blank=True)
    additional_diagnoses = models.JSONField(default=list, blank=True)
    medication_history = models.JSONField(default=list, blank=True)
    patient_records = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.medication_name} — {self.patient}"


class CarePlan(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="care_plan"
    )
    content = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    # Not in schema spec; needed for existing API error responses on failed status.
    error = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "careplan"

    def __str__(self) -> str:
        return f"CarePlan {self.order_id} — {self.status}"
