from hack.integration_tests.base import PatchedRequest


_base_url = "http://rest-server"


# ------------- ACCESS -------------

def make_register():
    return PatchedRequest(
        method="POST",
        url=_base_url + "/register",
    )

def make_login():
    return PatchedRequest(
        method="POST",
        url=_base_url + "/login",
    )

def make_login_recovery():
    return PatchedRequest(
        method="POST",
        url=_base_url + "/login/recovery",
    )


def make_login_recovery_submit():
    return PatchedRequest(
        method="POST",
        url=_base_url + "/login/recovery/submit",
    )


def make_registration_verification():
    return PatchedRequest(
        method="POST",
        url=_base_url + "/register/verification",
    )


def make_intercept_verification_code():
    return PatchedRequest(
        method="GET",
        url=_base_url + "/debug/intercept-verification-code",
    )


def make_intercept_recovery_token():
    return PatchedRequest(
        method="GET",
        url=_base_url + "/debug/intercept-recovery-token",
    )


def make_change_role():
    return PatchedRequest(
        method="POST",
        url=_base_url + "/debug/change-role",
    )


def make_get_active_login():
    return PatchedRequest(
        method="GET",
        url=_base_url + "/login",
    )


# ---------- LEAD SOURCES ----------

def make_create_lead_source() -> PatchedRequest:
    return PatchedRequest(
        method="POST",
        url=_base_url + "/lead-sources",
    )


def make_list_lead_sources() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/lead-sources",
    )


def make_get_lead_source() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/lead-sources/{lead_source_id}",
    )


def make_update_lead_source() -> PatchedRequest:
    return PatchedRequest(
        method="PUT",
        url=_base_url + "/lead-sources/{lead_source_id}",
    )


def make_delete_lead_source() -> PatchedRequest:
    return PatchedRequest(
        method="DELETE",
        url=_base_url + "/lead-sources/{lead_source_id}",
    )


# ---------- LEAD SOURCE ↔ OPERATOR (LeadSourceOperator) ----------

def make_create_lead_source_operator() -> PatchedRequest:
    return PatchedRequest(
        method="POST",
        url=_base_url + "/lead-sources/{lead_source_id}/operators",
    )


def make_list_lead_source_operators() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/lead-sources/{lead_source_id}/operators",
    )


def make_get_lead_source_operator() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/lead-sources/{lead_source_id}/operators/{lead_source_operator_id}",
    )


def make_update_lead_source_operator() -> PatchedRequest:
    return PatchedRequest(
        method="PUT",
        url=_base_url + "/lead-sources/{lead_source_id}/operators/{lead_source_operator_id}",
    )


def make_delete_lead_source_operator() -> PatchedRequest:
    return PatchedRequest(
        method="DELETE",
        url=_base_url + "/lead-sources/{lead_source_id}/operators/{lead_source_operator_id}",
    )


# ---------- OPERATORS ----------

def make_create_operator() -> PatchedRequest:
    return PatchedRequest(
        method="POST",
        url=_base_url + "/operators",
    )


def make_list_operators() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/operators",
    )


def make_get_operator() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/operators/{operator_id}",
    )


def make_update_operator() -> PatchedRequest:
    return PatchedRequest(
        method="PUT",
        url=_base_url + "/operators/{operator_id}",
    )


def make_delete_operator() -> PatchedRequest:
    return PatchedRequest(
        method="DELETE",
        url=_base_url + "/operators/{operator_id}",
    )


# ---------- APPEALS ----------

def make_create_appeal() -> PatchedRequest:
    return PatchedRequest(
        method="POST",
        url=_base_url + "/appeals",
    )


def make_list_appeals() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/appeals",
    )


def make_get_appeal() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/appeals/{appeal_id}",
    )


def make_update_appeal() -> PatchedRequest:
    return PatchedRequest(
        method="PUT",
        url=_base_url + "/appeals/{appeal_id}",
    )


def make_delete_appeal() -> PatchedRequest:
    return PatchedRequest(
        method="DELETE",
        url=_base_url + "/appeals/{appeal_id}",
    )


# ---------- INSPECT ----------

def make_inspect_leads() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/inspect/leads",
    )


def make_inspect_appeals_distribution() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/inspect/appeals-distribution",
    )


# ---------- USERS ----------

def make_list_users() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/users",
    )


def make_update_user() -> PatchedRequest:
    return PatchedRequest(
        method="PUT",
        url=_base_url + "/users/{user_id}",
    )


def make_delete_user() -> PatchedRequest:
    return PatchedRequest(
        method="DELETE",
        url=_base_url + "/users/{user_id}",
    )


def make_reset_user_password() -> PatchedRequest:
    return PatchedRequest(
        method="POST",
        url=_base_url + "/users/{user_id}/reset-password",
    )


# ---------- EVENTS ----------

def make_create_event() -> PatchedRequest:
    return PatchedRequest(
        method="POST",
        url=_base_url + "/events",
    )


def make_list_events() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/events",
    )


def make_get_event() -> PatchedRequest:
    return PatchedRequest(
        method="GET",
        url=_base_url + "/events/{event_id}",
    )


def make_update_event() -> PatchedRequest:
    return PatchedRequest(
        method="PUT",
        url=_base_url + "/events/{event_id}",
    )
