from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from core.models import UserProfile, StudentProfile, ProfessorProfile, TAProfile


class Command(BaseCommand):
    help = 'Fixes issues with user profiles and ensures consistency'

    def handle(self, *args, **options):
        self.stdout.write("Checking user profiles for issues...")

        # Ensure groups exist
        student_group, _ = Group.objects.get_or_create(name='Students')
        professor_group, _ = Group.objects.get_or_create(name='Professors')
        ta_group, _ = Group.objects.get_or_create(name='TAs')

        # Get all users
        users = User.objects.all()
        self.stdout.write(f"Found {users.count()} users")

        # Check each user
        for user in users:
            self.stdout.write(f"Checking user: {user.username}")

            # Ensure UserProfile exists
            try:
                profile = UserProfile.objects.get(user=user)
                self.stdout.write(f"  - UserProfile exists")
            except UserProfile.DoesNotExist:
                self.stdout.write(f"  - Creating missing UserProfile")
                profile = UserProfile.objects.create(user=user)

            # Check if they have a role profile
            has_role = False

            # Check for StudentProfile
            try:
                StudentProfile.objects.get(user_profile=profile)
                self.stdout.write(f"  - Has StudentProfile")
                has_role = True
                # Ensure they're in the Students group
                if not user.groups.filter(name='Students').exists():
                    user.groups.add(student_group)
                    self.stdout.write(f"  - Added to Students group")
            except StudentProfile.DoesNotExist:
                self.stdout.write(f"  - No StudentProfile")

            # Check for ProfessorProfile
            try:
                ProfessorProfile.objects.get(user_profile=profile)
                self.stdout.write(f"  - Has ProfessorProfile")
                has_role = True
                # Ensure they're in the Professors group
                if not user.groups.filter(name='Professors').exists():
                    user.groups.add(professor_group)
                    self.stdout.write(f"  - Added to Professors group")
            except ProfessorProfile.DoesNotExist:
                self.stdout.write(f"  - No ProfessorProfile")

            # Check for TAProfile
            try:
                TAProfile.objects.get(user_profile=profile)
                self.stdout.write(f"  - Has TAProfile")
                has_role = True
                # Ensure they're in the TAs group
                if not user.groups.filter(name='TAs').exists():
                    user.groups.add(ta_group)
                    self.stdout.write(f"  - Added to TAs group")
            except TAProfile.DoesNotExist:
                self.stdout.write(f"  - No TAProfile")

            # If they have no role, make them a student
            if not has_role:
                self.stdout.write(
                    f"  - No role profile found, creating StudentProfile")
                try:
                    student_profile = StudentProfile.objects.create(
                        user_profile=profile)
                    # Add to Students group
                    user.groups.add(student_group)
                    self.stdout.write(
                        f"  - Created StudentProfile and added to Students group")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"  - Error creating StudentProfile: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(
            "Profile check and fix completed"))
