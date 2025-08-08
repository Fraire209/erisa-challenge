import json
from django.core.management.base import BaseCommand
from claims.models import Claim, ClaimDetail

class Command(BaseCommand):
    help = "Load claims and claim details from JSON files"

    def handle(self, *args, **kwargs):
        # Load Claims
        with open('data/claim_list_data.json', 'r') as f:
            claims_data = json.load(f)
            for item in claims_data:
                Claim.objects.update_or_create(
                    claim_id=item['id'],
                    defaults={
                        'patient_name': item['patient_name'],
                        'billed_amount': item['billed_amount'],
                        'paid_amount': item['paid_amount'],
                        'status': item['status'],
                        'insurer_name': item['insurer_name'],
                        'discharge_date': item['discharge_date'],
                    }
                )

        # Load Claim Details
        with open('data/claim_detail_data.json', 'r') as f:
            details_data = json.load(f)
            for item in details_data:
                try:
                    claim = Claim.objects.get(claim_id=item['claim_id'])
                    ClaimDetail.objects.update_or_create(
                        id=item['id'],      #django partition key
                        defaults={
                            'claim': claim,    #will show the PK of the matching claim in the "claims.claim" table
                            'claim_id_original': item['claim_id'],  # keep original ID in table
                            'denial_reason': item['denial_reason'],
                            'cpt_codes': item['cpt_codes'],
                        }
                    )
                except Claim.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"Claim ID {item['claim_id']} not found. Skipping."
                    ))

        self.stdout.write(self.style.SUCCESS("Claims and details loaded successfully!"))
