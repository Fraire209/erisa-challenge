from django.db import models #should this be on here twice??

# Create your models here.
from django.db import models

class Claim(models.Model):
    claim_id = models.IntegerField(unique=True)           # from JSON 'id'
    patient_name = models.CharField(max_length=255)
    billed_amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=50)
    insurer_name = models.CharField(max_length=255)
    discharge_date = models.DateField()

    def __str__(self):
        return f"Claim {self.claim_id} - {self.patient_name}"
