# Create your models here.
from django.db import models
from django.contrib.auth.models import User
#Table schema for claim list
class Claim(models.Model):
    claim_id = models.IntegerField(unique=True)          
    patient_name = models.CharField(max_length=255)
    billed_amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=50)
    insurer_name = models.CharField(max_length=255)
    discharge_date = models.DateField()

    def __str__(self):
        return f"Claim {self.claim_id} - {self.patient_name}"
    
#Table schema for claim detail data, data can cbe accessed from claim.details.all
class ClaimDetail(models.Model):
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="details") #links this table to the matching claim in the "claims.claim" table. The FK will be a auto generated incremental number starting from 1
    denial_reason = models.TextField(blank=True, null=True)
    cpt_codes = models.CharField(max_length=255)  # Storing comma-separated codes

    def __str__(self):
        return f"Details for Claim {self.claim.claim_id}"

#Table schema for claim notes, linked to Claim by fk and user fk
class Note(models.Model):
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="notes")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes", null=True, blank=True)

    def __str__(self):
        return f"Note for Claim {self.claim.claim_id} - {self.text[:20]}"

#Table shema for claim flags, also linked to Claim
class SystemFlag(models.Model):
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="flags")
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.claim.id} - {self.message}"
