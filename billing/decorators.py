"""
billing/decorators.py
---------------------
Authentication and role-based access control decorators.

Usage:
    @billing_required
    def my_view(request): ...

    @role_required(['owner', 'manager'])
    def manager_only_view(request): ...
"""

from functools import wraps

from django.shortcuts import redirect


BILLING_LOGIN_URL = '/billing/login/'


def billing_required(view_func):
    """
    Require:
      1. User is logged in.
      2. User has an active StaffProfile.
    Redirects to /billing/login/ otherwise.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{BILLING_LOGIN_URL}?next={request.path}')
        try:
            profile = request.user.staff_profile
            if not profile.is_active:
                raise AttributeError
        except AttributeError:
            return redirect(BILLING_LOGIN_URL)
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(allowed_roles: list):
    """
    Require the user's StaffProfile.role to be in *allowed_roles*.
    Must be used AFTER @billing_required.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(BILLING_LOGIN_URL)
            try:
                role = request.user.staff_profile.role
            except AttributeError:
                return redirect(BILLING_LOGIN_URL)
            if role not in allowed_roles:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(
                    "You don't have permission to access this page."
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
