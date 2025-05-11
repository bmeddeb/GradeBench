from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Sets up the database tables for Canvas groups'

    def add_column_if_not_exists(self, cursor, table, column, definition):
        # Check if column exists
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if column not in column_names:
            self.stdout.write(f"Adding column {column} to {table}")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition};")
        else:
            self.stdout.write(f"Column {column} already exists in {table}")

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Create Canvas Group Category table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS "lms_canvasgroupcategory" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "canvas_id" integer unsigned NOT NULL UNIQUE,
                "name" varchar(255) NOT NULL,
                "self_signup" varchar(50) NULL,
                "auto_leader" varchar(50) NULL,
                "group_limit" integer NULL,
                "created_at" datetime NULL,
                "last_synced_at" datetime NOT NULL,
                "course_id" bigint NOT NULL REFERENCES "lms_canvascourse" ("id") DEFERRABLE INITIALLY DEFERRED
            );
            """)

            # Create Canvas Group table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS "lms_canvasgroup" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "canvas_id" integer unsigned NOT NULL UNIQUE,
                "name" varchar(255) NOT NULL,
                "description" text NULL,
                "created_at" datetime NULL,
                "last_synced_at" datetime NOT NULL,
                "category_id" bigint NOT NULL REFERENCES "lms_canvasgroupcategory" ("id") DEFERRABLE INITIALLY DEFERRED,
                "core_team_id" bigint NULL REFERENCES "core_team" ("id") DEFERRABLE INITIALLY DEFERRED
            );
            """)

            # Create Canvas Group Membership table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS "lms_canvasgroupmembership" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "user_id" integer unsigned NOT NULL,
                "name" varchar(255) NOT NULL,
                "email" varchar(254) NULL,
                "added_at" datetime NOT NULL,
                "group_id" bigint NOT NULL REFERENCES "lms_canvasgroup" ("id") DEFERRABLE INITIALLY DEFERRED,
                "student_id" bigint NULL REFERENCES "core_student" ("id") DEFERRABLE INITIALLY DEFERRED,
                UNIQUE ("group_id", "user_id")
            );
            """)

            # Add new fields to Team model if they don't exist
            self.add_column_if_not_exists(
                cursor,
                '"core_team"',
                '"canvas_course_id"',
                'bigint NULL REFERENCES "lms_canvascourse" ("id") DEFERRABLE INITIALLY DEFERRED'
            )

            self.add_column_if_not_exists(
                cursor,
                '"core_team"',
                '"canvas_group_id"',
                'integer unsigned NULL'
            )

            self.add_column_if_not_exists(
                cursor,
                '"core_team"',
                '"last_synced_at"',
                'datetime NULL'
            )

            # Create index on Team
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS "core_team_canvas__d57672_idx"
            ON "core_team" ("canvas_course_id", "canvas_group_id");
            """)

            self.stdout.write(self.style.SUCCESS('Successfully set up Canvas groups tables'))