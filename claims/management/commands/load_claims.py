import json
import csv
import os
from django.core.management.base import BaseCommand
from claims.models import Claim, ClaimDetail

class Command(BaseCommand):
    help = "Load claims and claim details from JSON or CSV files automatically"

    #data stored in this folder
    DATA_DIR = 'data'

    def handle(self, *args, **kwargs):
        # find existing file with .json or .csv
        def find_file(base_name):
            for ext in ['.json', '.csv']:
                file_path = os.path.join(self.DATA_DIR, base_name + ext)
                if os.path.exists(file_path):
                    return file_path
            return None

        #loads JSON or CSV, will always choose json over csv based on loop logic
        def load_file(file_path):
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    return json.load(f)
            elif file_path.endswith('.csv'):
                with open(file_path, 'r', newline='') as f:
                    return list(csv.DictReader(f, delimiter='|'))   #files uses pipe delimiters
            else:
                return []

        # Find and load claim list
        claim_file = find_file('claim_list_data')
        #error case
        if not claim_file:
            self.stdout.write(self.style.ERROR("No claim_list_data file found."))
            return
        claims_data = load_file(claim_file)

        for item in claims_data:
            # Convert numeric fields from CSV if necessary
            billed_amount = float(item['billed_amount'])
            paid_amount = float(item['paid_amount'])
            
            Claim.objects.update_or_create(
                claim_id=int(item['id']),                   #if claim id exists it updates, else it creates
                defaults={
                    'patient_name': item['patient_name'],
                    'billed_amount': billed_amount,
                    'paid_amount': paid_amount,
                    'status': item['status'],
                    'insurer_name': item['insurer_name'],
                    'discharge_date': item['discharge_date'],
                }
            )

        # Find and load claim details
        detail_file = find_file('claim_detail_data')
        if not detail_file:
            self.stdout.write(self.style.WARNING("No claim_detail_data file found. Skipping details."))
            return
        details_data = load_file(detail_file)

        for item in details_data:
            try:
                claim = Claim.objects.get(claim_id=int(item['claim_id'])) #finds matching claim from id in claims table
                ClaimDetail.objects.update_or_create(
                    id=int(item['id']),
                    defaults={
                        'claim': claim,
                        'denial_reason': item['denial_reason'],
                        'cpt_codes': item['cpt_codes'],
                    }
                )
            except Claim.DoesNotExist:                          #no matching claim id case
                self.stdout.write(self.style.WARNING(
                    f"Claim ID {item['claim_id']} not found. Skipping."
                ))

        self.stdout.write(self.style.SUCCESS("Claims and details loaded successfully!"))
