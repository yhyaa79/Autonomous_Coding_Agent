from functools import wraps
from typing import Callable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest, JsonResponse

User = get_user_model()


def _legacy_api_token_ok(request: HttpRequest) -> bool:
    expected = getattr(settings, "AGENT_API_TOKEN", "") or ""
    if not expected:
        return True
    header = request.headers.get("X-ACA-Token") or request.META.get("HTTP_X_ACA_TOKEN")
    return header == expected


def require_user(view_func: Callable):
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        if _legacy_api_token_ok(request):
            return view_func(request, *args, **kwargs)
        return JsonResponse({"error": "ورود لازم است"}, status=401)

    return wrapper


def projects_queryset(request):
    from .models import Project

    if request.user.is_authenticated:
        return Project.objects.filter(owner=request.user)
    return Project.objects.all()


def conversation_owned(request, conv) -> bool:
    if request.user.is_authenticated:
        return conv.project.owner_id == request.user.id
    return True


def billing_user(request):
    if request.user.is_authenticated:
        return request.user
    return None
