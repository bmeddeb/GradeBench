from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json


@login_required
def wizard_view(request):
    """
    View for the Canvas Group to Core Team Sync Wizard.
    Renders a multi-step wizard interface for synchronizing Canvas Groups to Core Teams.
    Fetches real data from the database.
    """
    # Wizard view for Canvas Group to Core Team Sync
    # Import Canvas models here to avoid potential circular imports
    from lms.canvas.models import CanvasCourse, CanvasGroupCategory, CanvasGroup
    import json

    # Initialize wizard session if not exists
    if 'wizard_data' not in request.session:
        request.session['wizard_data'] = {
            'current_step': 1,
            'course_id': None,
            'sync_memberships': True,
            'sync_leaders': False,
            'group_set_ids': [],
            'group_ids': [],
            'create_github_repo': False,
            'setup_project_management': False,
            'repo_pattern': '{course_code}-{group_name}',
            'confirmed': False
        }

    # Get the current step from the session, default to 1
    wizard_data = request.session['wizard_data']
    current_step = wizard_data.get('current_step', 1)

    # Always start at step 1 for GET requests with no query string
    # This fixes the issue of jumping to results page
    if request.method == 'GET' and not request.GET:
        current_step = 1
        wizard_data['current_step'] = 1
        request.session.modified = True

    # Process form submission if this is a POST request
    if request.method == 'POST':
        action = request.POST.get('action', '')
        # Process form submission with action

        # Update wizard data based on form submission
        if current_step == 1:
            if 'course_id' in request.POST:
                wizard_data['course_id'] = request.POST.get('course_id')
            if 'sync_memberships' in request.POST:
                wizard_data['sync_memberships'] = True
            else:
                wizard_data['sync_memberships'] = False
            if 'sync_leaders' in request.POST:
                wizard_data['sync_leaders'] = True
            else:
                wizard_data['sync_leaders'] = False

        elif current_step == 2:
            group_set_ids = request.POST.getlist('group_set_ids')
            wizard_data['group_set_ids'] = group_set_ids

        elif current_step == 3:
            group_ids = request.POST.getlist('group_ids')
            wizard_data['group_ids'] = group_ids

        elif current_step == 4:
            if 'create_github_repo' in request.POST:
                wizard_data['create_github_repo'] = True
            else:
                wizard_data['create_github_repo'] = False
            if 'setup_project_management' in request.POST:
                wizard_data['setup_project_management'] = True
            else:
                wizard_data['setup_project_management'] = False
            if 'repo_pattern' in request.POST:
                wizard_data['repo_pattern'] = request.POST.get('repo_pattern')

        elif current_step == 5:
            if 'confirmed' in request.POST:
                wizard_data['confirmed'] = True

        # Handle navigation between steps
        if action == 'next':
            current_step += 1
        elif action == 'previous':
            current_step -= 1
        elif action == 'reset':
            # Reset the wizard data
            wizard_data = {
                'current_step': 1,
                'course_id': None,
                'sync_memberships': True,
                'sync_leaders': False,
                'group_set_ids': [],
                'group_ids': [],
                'create_github_repo': False,
                'setup_project_management': False,
                'repo_pattern': '{course_code}-{group_name}',
                'confirmed': False
            }
            current_step = 1
        elif action == 'finish':
            # Process the final submission - create teams from selected groups
            if wizard_data.get('confirmed'):
                group_ids = wizard_data.get('group_ids', [])
                sync_memberships = wizard_data.get('sync_memberships', True)
                sync_leaders = wizard_data.get('sync_leaders', False)

                # Create teams for each selected group
                created_teams = []
                for group_id in group_ids:
                    try:
                        canvas_group = CanvasGroup.objects.get(
                            canvas_id=group_id)

                        # Check if a team already exists for this group
                        from core.models import Team
                        existing_team = Team.objects.filter(
                            canvas_group_id=group_id).first()

                        if existing_team:
                            # Update existing team
                            created_teams.append({
                                'id': existing_team.id,
                                'name': existing_team.name,
                                'status': 'updated',
                                'member_count': existing_team.students.count()
                            })
                        else:
                            # Create new team
                            team = Team.objects.create(
                                name=canvas_group.name,
                                canvas_course=canvas_group.category.course,
                                canvas_group_id=canvas_group.canvas_id,
                                canvas_group_set_id=canvas_group.category.canvas_id,
                                canvas_group_set_name=canvas_group.category.name
                            )

                            # Sync memberships if requested
                            if sync_memberships:
                                # This would be implemented in a real application
                                pass

                            created_teams.append({
                                'id': team.id,
                                'name': team.name,
                                'status': 'created',
                                'member_count': 0  # New team has no members yet
                            })
                    except CanvasGroup.DoesNotExist:
                        continue

                # Save created teams to session for display in results
                wizard_data['created_teams'] = created_teams

            # Move to results page
            current_step = 6

        # Ensure step is within valid range
        if current_step < 1:
            current_step = 1
        elif current_step > 6:
            current_step = 6

        # Update session
        wizard_data['current_step'] = current_step
        request.session['wizard_data'] = wizard_data
        request.session.modified = True

        # For AJAX requests, return JSON with step data
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Prepare step data for the client
            step_data = {}

            # Prepare any step-specific data based on current_step
            if current_step == 1:  # Course Selection
                # Return courses
                courses = []
                for course in CanvasCourse.objects.all():
                    courses.append({
                        'canvas_id': course.canvas_id,
                        'course_code': course.course_code,
                        'name': course.name
                    })
                # Convert to JSON string to ensure proper serialization
                step_data['courses'] = json.dumps(courses)

            elif current_step == 2:  # Group Set Selection
                # Return group sets for selected course
                course_id = wizard_data.get('course_id')
                group_sets = []

                if course_id:
                    for group_set in CanvasGroupCategory.objects.filter(course__canvas_id=course_id):
                        group_sets.append({
                            'canvas_id': group_set.canvas_id,
                            'name': group_set.name,
                            'group_count': group_set.groups.count()
                        })

                step_data['group_sets'] = json.dumps(group_sets)

            elif current_step == 3:  # Group Selection
                # Return groups for selected group sets
                group_set_ids = wizard_data.get('group_set_ids', [])
                groups = []

                if group_set_ids:
                    # Convert to integers
                    int_group_set_ids = []
                    for id_val in group_set_ids:
                        try:
                            int_group_set_ids.append(int(id_val))
                        except (ValueError, TypeError):
                            pass

                    # Query groups
                    for group in CanvasGroup.objects.filter(category__canvas_id__in=int_group_set_ids):
                        groups.append({
                            'canvas_id': group.canvas_id,
                            'name': group.name,
                            'category_id': group.category.canvas_id,
                            'category_name': group.category.name,
                            'members_count': group.memberships.count()
                        })

                step_data['groups'] = json.dumps(groups)

            elif current_step == 6:  # Results
                # Return created teams - be sure to serialize any Python objects to JSON
                created_teams = wizard_data.get('created_teams', [])
                # Make sure all values are JSON serializable (e.g., booleans)
                step_data['created_teams'] = json.dumps(created_teams)

            # Return JSON response with updated wizard data
            return JsonResponse({
                'status': 'success',
                'current_step': current_step,
                'wizard_data': {
                    'current_step': current_step,
                    **step_data
                }
            })

    # Context data for the template
    context = {
        'progress_labels': [
            'Course Selection', 'Group Set Selection',
            'Group Selection', 'Integration Config',
            'Confirmation', 'Results'
        ],
        'current_step': current_step,
        'back_enabled': current_step > 1,
        'next_enabled': True,
        'wizard_data': wizard_data,
        # Convert Python booleans to JavaScript strings for JS usage
        'debug': 'true' if settings.DEBUG else 'false',
        # Also provide regular Python boolean for Django template usage
        'debug_mode': settings.DEBUG
    }

    # Add step-specific data based on real database data
    if current_step == 1:
        # Fetch actual Canvas courses from the database
        courses = []
        try:
            # Query the database for courses
            query_set = CanvasCourse.objects.all().order_by('canvas_id')

            # Process course data
            for course in query_set:
                courses.append({
                    'canvas_id': course.canvas_id,
                    'course_code': course.course_code,
                    'name': course.name
                })
        except Exception as e:
            # Handle database errors gracefully
            courses = []

        # Convert to JSON for JavaScript
        courses_json = json.dumps(courses)

        context['step_data'] = {
            'courses': courses,  # For Django template
            'courses_json': courses_json  # For JavaScript
        }

        # Add a flag to indicate if courses exist
        context['has_courses'] = len(courses) > 0

    elif current_step == 2:
        # Get selected course from session
        course_id = wizard_data.get('course_id')

        # Fetch group sets for the selected course
        group_sets = []
        if course_id:
            try:
                for group_set in CanvasGroupCategory.objects.filter(course__canvas_id=course_id):
                    group_sets.append({
                        'canvas_id': group_set.canvas_id,
                        'name': group_set.name,
                        'group_count': group_set.groups.count()
                    })
            except Exception:
                # Handle database errors gracefully
                pass

        # Convert to JSON for JavaScript
        group_sets_json = json.dumps(group_sets)

        # Add a flag to indicate if group sets exist
        context['has_group_sets'] = len(group_sets) > 0

        context['step_data'] = {
            'group_sets': group_sets,  # For Django template
            'group_sets_json': group_sets_json  # For JavaScript
        }

    elif current_step == 3:
        # Get selected group sets from session
        group_set_ids = wizard_data.get('group_set_ids', [])

        # Fetch groups for the selected group sets directly from database
        groups = []
        if group_set_ids:
            # Convert string IDs to integers if needed
            int_group_set_ids = []
            for id_val in group_set_ids:
                try:
                    int_group_set_ids.append(int(id_val))
                except (ValueError, TypeError):
                    # Skip invalid IDs
                    pass

            try:
                # Query actual groups from database
                for group in CanvasGroup.objects.filter(category__canvas_id__in=int_group_set_ids):
                    groups.append({
                        'canvas_id': group.canvas_id,
                        'name': group.name,
                        'category_id': group.category.canvas_id,
                        'category_name': group.category.name,
                        'members_count': group.memberships.count()
                    })
            except Exception:
                # Handle database errors gracefully
                pass

        # Convert to JSON for JavaScript
        groups_json = json.dumps(groups)

        # Add a flag to indicate if groups exist
        context['has_groups'] = len(groups) > 0

        context['step_data'] = {
            'groups': groups,  # For Django template
            'groups_json': groups_json  # For JavaScript
        }

    elif current_step == 6:
        # Results page - show created teams
        created_teams = wizard_data.get('created_teams', [])

        # Convert to JSON for JavaScript
        created_teams_json = json.dumps(created_teams)

        context['step_data'] = {
            'created_teams': created_teams,  # For Django template
            'created_teams_json': created_teams_json  # For JavaScript
        }

        # Debug - print final step_data
        print("\nFinal created_teams step_data:", context['step_data'])

    # Render the appropriate template
    return render(request, 'wizard/wizard_main.html', context)
