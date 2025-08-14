from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps

class Command(BaseCommand):
    help = 'Clears all rows from a table and resets its auto-increment ID'

    def add_arguments(self, parser):
        parser.add_argument('model', type=str, help='App label and model name, e.g., myapp.Note')

    def handle(self, *args, **options):
        model_path = options['model']
        try:
            app_label, model_name = model_path.split('.')
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError):
            self.stderr.write(self.style.ERROR('Invalid model. Use format: app_label.ModelName'))
            return

        # Delete all rows
        model.objects.all().delete()

        # Reset auto-increment
        table_name = model._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name=%s;", [table_name])

        self.stdout.write(self.style.SUCCESS(f'Table {table_name} cleared and auto-increment reset.'))
