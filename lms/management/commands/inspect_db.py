from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Inspects the database schema'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            self.stdout.write(f"Tables in the database: {tables}")
            
            # Check CanvasEnrollment table structure
            cursor.execute("PRAGMA table_info(lms_canvasenrollment);")
            columns = cursor.fetchall()
            self.stdout.write(f"Columns in lms_canvasenrollment: {columns}")