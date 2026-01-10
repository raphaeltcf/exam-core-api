import time

from django.core.management import BaseCommand
from django.db import OperationalError, connection


class Command(BaseCommand):

    def handle(self, *args, **options):
        has_establish_db_connection = False

        self.stdout.write("Waiting for the database to become available...")

        max_seconds_to_wait = 60
        for _ in range(max_seconds_to_wait):
            try:
                connection.ensure_connection()
                has_establish_db_connection = True
                break
            except OperationalError:
                self.stdout.write("Still waiting for database connection, waiting 1 second...")
                time.sleep(1)

        if has_establish_db_connection:
            self.stdout.write(self.style.SUCCESS("Database is available!"))
        else:
            self.stderr.write(self.style.ERROR("Error! It was not possible to establish the connection."))
            exit(1)
