from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from core.models import UserProfile, ProfessorProfile, TAProfile, Student


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

            # If they have no role, add them to Students group
            if not has_role:
                # Add to Students group
                if not user.groups.filter(name='Students').exists():
                    user.groups.add(student_group)
                    self.stdout.write(f"  - Added to Students group")
                
                # Check if there's a corresponding Student record
                try:
                    student = Student.objects.get(email=user.email)
                    self.stdout.write(f"  - Corresponding Student record exists")
                except Student.DoesNotExist:
                    self.stdout.write(f"  - Creating Student record")
                    try:
                        student = Student.objects.create(
                            first_name=user.first_name or "Unknown",
                            last_name=user.last_name or "User",
                            email=user.email,
                            github_username=profile.github_username,
                            created_by=user
                        )
                        self.stdout.write(f"  - Created Student record")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"  - Error creating Student record: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(
            "Profile check and fix completed"))
