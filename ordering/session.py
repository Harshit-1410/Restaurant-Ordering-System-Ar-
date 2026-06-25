"""
ordering/session.py
-------------------
Stateless helpers for token-based table sessions and per-browser customer sessions.
Imported by both ordering/views.py and restaurants/views.py to avoid circular
imports and keep session logic in one place.
"""

import secrets

from .models import CustomerSession, Table, TableSession

# Django session key that stores the active CustomerSession PK
SESSION_KEY = 'customer_session_id'


# ── Browser UUID ──────────────────────────────────────────────────────────────

def get_or_create_browser_uuid(request):
    """
    Return a stable random identifier for this browser.
    Generated once per Django session and stored server-side; never sent raw
    to the client, so it cannot be spoofed via a URL parameter.
    """
    uuid = request.session.get('browser_uuid')
    if not uuid:
        uuid = secrets.token_urlsafe(16)
        request.session['browser_uuid'] = uuid
    return uuid


# ── QR token → CustomerSession ────────────────────────────────────────────────

def join_table(request, qr_token: str):
    """
    Validate a QR token, find-or-create the active TableSession for that table,
    and find-or-create a CustomerSession for this browser within that session.

    Stores the CustomerSession PK in the Django server-side session so all
    subsequent requests (cart, order, bill) can look it up without trusting
    any URL parameter.

    Returns:
        (CustomerSession, None)   on success
        (None, 'invalid_token')   if the token is unknown or the table is inactive
    """
    try:
        table = Table.objects.select_related('restaurant').get(
            qr_token=qr_token, is_active=True
        )
    except Table.DoesNotExist:
        return None, 'invalid_token'

    # Reuse an existing open session or start a fresh one
    table_session = (
        TableSession.objects
        .filter(table=table, status=TableSession.STATUS_OPEN)
        .first()
    )
    if not table_session:
        table_session = TableSession.objects.create(table=table)

    browser_uuid = get_or_create_browser_uuid(request)

    customer_session, _ = CustomerSession.objects.get_or_create(
        table_session=table_session,
        browser_uuid=browser_uuid,
    )

    # Bind this browser to its CustomerSession for the lifetime of the visit
    request.session[SESSION_KEY] = customer_session.id
    return customer_session, None


# ── Active session lookup ─────────────────────────────────────────────────────

def get_active_customer_session(request):
    """
    Look up the CustomerSession stored in this request's Django session.

    Returns None when:
    - No session has been created (user hasn't scanned a QR yet).
    - The stored ID no longer exists.
    - The underlying TableSession has been closed / paid.
    """
    cs_id = request.session.get(SESSION_KEY)
    if not cs_id:
        return None
    try:
        return (
            CustomerSession.objects
            .select_related('table_session__table__restaurant')
            .get(id=cs_id, table_session__status=TableSession.STATUS_OPEN)
        )
    except CustomerSession.DoesNotExist:
        return None
