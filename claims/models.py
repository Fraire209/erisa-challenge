from django.db import models #should this be on here twice??

# Create your models here.
from django.db import models

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

