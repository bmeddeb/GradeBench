from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
import json


class WizardView(LoginRequiredMixin, View):
    def get(self, request):
        from lms.canvas.models import CanvasCourse, CanvasGroupCategory, CanvasGroup
        # Initialize wizard session if not exists
        if 'wizard_data' not in request.session:
            request.session['wizard_data'] = {
                'current_step': 1,
                'course_id': None,
                'group_set_ids': [],
                'group_ids': [],
                'create_github_repo': False,
                'setup_project_management': False,
                'repo_pattern': '{course_code}-{group_name}',
                'confirmed': False
            }
        wizard_data = request.session['wizard_data']
        current_step = wizard_data.get('current_step', 1)
        if not request.GET:
            current_step = 1
            wizard_data['current_step'] = 1
            request.session.modified = True
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
            'debug': 'true' if settings.DEBUG else 'false',
            'debug_mode': settings.DEBUG
        }
        if current_step == 1:
            courses = []
            try:
                query_set = CanvasCourse.objects.all().order_by('canvas_id')
                for course in query_set:
                    courses.append({
                        'canvas_id': course.canvas_id,
                        'course_code': course.course_code,
                        'name': course.name
                    })
            except Exception:
                courses = []
            courses_json = json.dumps(courses)
            context['step_data'] = {
                'courses': courses,
                'courses_json': courses_json
            }
            context['has_courses'] = len(courses) > 0
        elif current_step == 2:
            course_id = wizard_data.get('course_id')
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
                    pass
            group_sets_json = json.dumps(group_sets)
            context['has_group_sets'] = len(group_sets) > 0
            context['step_data'] = {
                'group_sets': group_sets,
                'group_sets_json': group_sets_json
            }
        elif current_step == 3:
            group_set_ids = wizard_data.get('group_set_ids', [])
            groups = []
            if group_set_ids:
                int_group_set_ids = []
                for id_val in group_set_ids:
                    try:
                        int_group_set_ids.append(int(id_val))
                    except (ValueError, TypeError):
                        pass
                try:
                    for group in CanvasGroup.objects.filter(category__canvas_id__in=int_group_set_ids):
                        groups.append({
                            'canvas_id': group.canvas_id,
                            'name': group.name,
                            'category_id': group.category.canvas_id,
                            'category_name': group.category.name,
                            'members_count': group.memberships.count()
                        })
                except Exception:
                    pass
            groups_json = json.dumps(groups)
            context['has_groups'] = len(groups) > 0
            context['step_data'] = {
                'groups': groups,
                'groups_json': groups_json
            }
        elif current_step == 6:
            created_teams = wizard_data.get('created_teams', [])
            created_teams_json = json.dumps(created_teams)
            context['step_data'] = {
                'created_teams': created_teams,
                'created_teams_json': created_teams_json
            }
            print("\nFinal created_teams step_data:", context['step_data'])
        return render(request, 'wizard/wizard_main.html', context)

    def post(self, request):
        from lms.canvas.models import CanvasCourse, CanvasGroupCategory, CanvasGroup
        action = request.POST.get('action', '')
        if 'wizard_data' not in request.session:
            request.session['wizard_data'] = {
                'current_step': 1,
                'course_id': None,
                'group_set_ids': [],
                'group_ids': [],
                'create_github_repo': False,
                'setup_project_management': False,
                'repo_pattern': '{course_code}-{group_name}',
                'confirmed': False
            }
        wizard_data = request.session['wizard_data']
        current_step = wizard_data.get('current_step', 1)
        if current_step == 1:
            if 'course_id' in request.POST:
                wizard_data['course_id'] = request.POST.get('course_id')
        elif current_step == 2:
            group_set_ids = request.POST.getlist('group_set_ids')
            wizard_data['group_set_ids'] = group_set_ids
        elif current_step == 3:
            group_ids = request.POST.getlist('group_ids')
            wizard_data['group_ids'] = group_ids
        elif current_step == 4:
            wizard_data['create_github_repo'] = 'create_github_repo' in request.POST
            wizard_data['setup_project_management'] = 'setup_project_management' in request.POST
            if 'repo_pattern' in request.POST:
                wizard_data['repo_pattern'] = request.POST.get('repo_pattern')
        elif current_step == 5:
            if 'confirmed' in request.POST:
                wizard_data['confirmed'] = True
        if action == 'next':
            current_step += 1
        elif action == 'previous':
            current_step -= 1
        elif action == 'reset':
            wizard_data = {
                'current_step': 1,
                'course_id': None,
                'group_set_ids': [],
                'group_ids': [],
                'create_github_repo': False,
                'setup_project_management': False,
                'repo_pattern': '{course_code}-{group_name}',
                'confirmed': False
            }
            current_step = 1
        elif action == 'finish':
            if wizard_data.get('confirmed'):
                group_ids = wizard_data.get('group_ids', [])
                created_teams = []
                for group_id in group_ids:
                    try:
                        canvas_group = CanvasGroup.objects.get(
                            canvas_id=group_id)
                        from core.models import Team
                        existing_team = Team.objects.filter(
                            canvas_group_id=group_id).first()
                        if existing_team:
                            created_teams.append({
                                'id': existing_team.id,
                                'name': existing_team.name,
                                'status': 'updated',
                                'member_count': existing_team.students.count()
                            })
                        else:
                            team = Team.objects.create(
                                name=canvas_group.name,
                                canvas_course=canvas_group.category.course,
                                canvas_group_id=canvas_group.canvas_id,
                                canvas_group_set_id=canvas_group.category.canvas_id,
                                canvas_group_set_name=canvas_group.category.name
                            )
                            created_teams.append({
                                'id': team.id,
                                'name': team.name,
                                'status': 'created',
                                'member_count': 0
                            })
                    except CanvasGroup.DoesNotExist:
                        continue
                wizard_data['created_teams'] = created_teams
            current_step = 6
        if current_step < 1:
            current_step = 1
        elif current_step > 6:
            current_step = 6
        wizard_data['current_step'] = current_step
        request.session['wizard_data'] = wizard_data
        request.session.modified = True
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            step_data = {}
            if current_step == 1:
                courses = []
                for course in CanvasCourse.objects.all():
                    courses.append({
                        'canvas_id': course.canvas_id,
                        'course_code': course.course_code,
                        'name': course.name
                    })
                step_data['courses'] = json.dumps(courses)
            elif current_step == 2:
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
            elif current_step == 3:
                group_set_ids = wizard_data.get('group_set_ids', [])
                groups = []
                if group_set_ids:
                    int_group_set_ids = []
                    for id_val in group_set_ids:
                        try:
                            int_group_set_ids.append(int(id_val))
                        except (ValueError, TypeError):
                            pass
                    for group in CanvasGroup.objects.filter(category__canvas_id__in=int_group_set_ids):
                        groups.append({
                            'canvas_id': group.canvas_id,
                            'name': group.name,
                            'category_id': group.category.canvas_id,
                            'category_name': group.category.name,
                            'members_count': group.memberships.count()
                        })
                step_data['groups'] = json.dumps(groups)
            elif current_step == 6:
                created_teams = wizard_data.get('created_teams', [])
                step_data['created_teams'] = json.dumps(created_teams)
            return JsonResponse({
                'status': 'success',
                'current_step': current_step,
                'wizard_data': {
                    'current_step': current_step,
                    **step_data
                }
            })
        return self.get(request)
