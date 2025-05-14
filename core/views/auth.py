from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import TemplateView
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User
from django.conf import settings
from core.models import UserProfile
import pytz
import json


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class StyleguideView(StaffRequiredMixin, TemplateView):
    template_name = "styleguide.html"


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["profile"] = self.request.user.profile
        return context


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, "core/login.html")


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        github_connected = False
        github_username = None
        social_auth = None
        try:
            social_auth = UserSocialAuth.objects.filter(
                user=user, provider="github"
            ).first()
            if social_auth:
                github_connected = True
            profile = user.profile
            if profile.github_username:
                github_username = profile.github_username
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)
        timezones = pytz.common_timezones
        return render(
            request,
            "core/profile.html",
            {
                "user": user,
                "profile": profile,
                "github_connected": github_connected,
                "github_username": github_username,
                "social_auth": social_auth,
                "timezones": timezones,
            },
        )

    def post(self, request):
        user = request.user
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)
        changes_made = False
        if user.first_name != request.POST.get("first_name", user.first_name):
            user.first_name = request.POST.get("first_name", user.first_name)
            changes_made = True
        if user.last_name != request.POST.get("last_name", user.last_name):
            user.last_name = request.POST.get("last_name", user.last_name)
            changes_made = True
        new_username = request.POST.get("username")
        if new_username and new_username != user.username:
            if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                messages.error(request, "That username is already taken.")
            else:
                user.username = new_username
                messages.success(request, "Username updated successfully.")
                changes_made = True
        email = request.POST.get("email")
        if email and email != user.email:
            user.email = email
            changes_made = True
        if profile.bio != request.POST.get("bio", profile.bio):
            profile.bio = request.POST.get("bio", profile.bio)
            changes_made = True
        phone_number = request.POST.get("phone_number")
        if phone_number and phone_number != profile.phone_number:
            profile.phone_number = phone_number
            changes_made = True
        timezone_val = request.POST.get("timezone")
        if timezone_val and timezone_val != profile.timezone:
            if timezone_val in pytz.common_timezones:
                profile.timezone = timezone_val
                changes_made = True
        user.save()
        profile.save()
        if changes_made and not messages.get_messages(request):
            messages.success(request, "Profile updated successfully.")
        return redirect("profile")


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "core/logout.html")

    def post(self, request):
        auth_logout(request)
        messages.success(request, "You have been successfully logged out.")
        return redirect("login")


class UpdateProfileAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            user = request.user
            profile = user.profile
            data = json.loads(request.body)
            changes_made = False
            if "first_name" in data and data["first_name"] != user.first_name:
                user.first_name = data["first_name"]
                changes_made = True
            if "last_name" in data and data["last_name"] != user.last_name:
                user.last_name = data["last_name"]
                changes_made = True
            if "username" in data and data["username"] != user.username:
                username_exists = (
                    User.objects.filter(username=data["username"])
                    .exclude(id=user.id)
                    .exists()
                )
                if username_exists:
                    return JsonResponse(
                        {"status": "error", "message": "That username is already taken"},
                        status=400,
                    )
                user.username = data["username"]
                changes_made = True
            if "email" in data and data["email"] != user.email:
                user.email = data["email"]
                changes_made = True
            if "bio" in data and data["bio"] != profile.bio:
                profile.bio = data["bio"]
                changes_made = True
            if "phone_number" in data and data["phone_number"] != profile.phone_number:
                profile.phone_number = data["phone_number"]
                changes_made = True
            if "timezone" in data and data["timezone"] != profile.timezone:
                if data["timezone"] in pytz.common_timezones:
                    profile.timezone = data["timezone"]
                    changes_made = True
            if changes_made:
                user.save()
                profile.save()
                return JsonResponse(
                    {"status": "success", "message": "Profile updated successfully"}
                )
            else:
                return JsonResponse(
                    {"status": "info", "message": "No changes were made to your profile"}
                )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
