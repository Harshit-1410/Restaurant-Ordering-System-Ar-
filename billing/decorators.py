"""
billing/decorators.py
---------------------
Authentication and role-based access control decorators shared between
the Billing Dashboard and the Kitchen Dashboard.

Roles and their access:
  owner   → billing + kitchen + reports + settings
  manager → billing + kitchen + reports
  cashier → billing only
  kitchen → kitchen only

Usage:
    @billing_required                         — owner / manager / cashier
    @kitchen_required                         — owner / manager / kitchen
    @role_required(['owner', 'manager'])      — explicit role whitelist
"""

from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect


BILLING_LOGIN_URL = '/billing/login/'
KITCHEN_LOGIN_URL = '/ordering/kitchen/login/'

# Role groups — single source of truth for permission checks
BILLING_ROLES = ('owner', 'manager', 'cashier')
KITCHEN_ROLES = ('owner', 'manager', 'kitchen')


def _get_profile(user):
    """
    Return the user's StaffProfile, or None if missing / inactive.
    Uses attribute access only — no import needed to avoid circular refs.
    """
    try:
        profile = user.staff_profile
        return profile if profile.is_active else None
    except AttributeError:
        return None


# ── Billing Dashboard ─────────────────────────────────────────────────────────

def billing_required(view_func):
    """
    Require:
      1. User is authenticated.
      2. User has an active StaffProfile.
      3. User's role is in BILLING_ROLES (owner / manager / cashier).
    Kitchen staff attempting billing access receive 403.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{BILLING_LOGIN_URL}?next={request.path}')
        profile = _get_profile(request.user)
        if profile is None:
            return redirect(BILLING_LOGIN_URL)
        if profile.role not in BILLING_ROLES:
            return HttpResponseForbidden(
                "Kitchen staff do not have access to the Billing Dashboard."
            )
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Kitchen Dashboard ─────────────────────────────────────────────────────────

def kitchen_required(view_func):
    """
    Require:
      1. User is authenticated.
      2. User has an active StaffProfile.
      3. User's role is in KITCHEN_ROLES (owner / manager / kitchen).
    Cashiers attempting kitchen access receive 403.
    Unauthenticated users are redirected to the kitchen login page.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{KITCHEN_LOGIN_URL}?next={request.path}')
        profile = _get_profile(request.user)
        if profile is None:
            return redirect(KITCHEN_LOGIN_URL)
        if profile.role not in KITCHEN_ROLES:
            return HttpResponseForbidden(
                "You do not have permission to access the Kitchen Dashboard."
            )
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Generic role whitelist ────────────────────────────────────────────────────

def role_required(allowed_roles: list):
    """
    Require the user's StaffProfile.role to be in *allowed_roles*.
    Must be composed with either @billing_required or @kitchen_required
    to ensure the user is authenticated first.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(BILLING_LOGIN_URL)
            profile = _get_profile(request.user)
            if profile is None or profile.role not in allowed_roles:
                return HttpResponseForbidden(
                    "You don't have permission to access this page."
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
