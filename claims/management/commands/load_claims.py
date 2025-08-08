import json
from datetime import datetime
from django.core.management.base import BaseCommand
from claims.models import Claim

class Command(BaseCommand):
    help = "Load claims from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']

        with open(json_file, 'r') as f:
            data = json.load(f)

        for item in data:
            claim, created = Claim.objects.update_or_create(
                claim_id=item['id'],
                defaults={
                    'patient_name': item['patient_name'],
                    'billed_amount': item['billed_amount'],
                    'paid_amount': item['paid_amount'],
                    'status': item['status'],
                    'insurer_name': item['insurer_name'],
                    'discharge_date': datetime.strptime(item['discharge_date'], '%Y-%m-%d').date(),
                }
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} claim {claim.claim_id} - {claim.patient_name}")
