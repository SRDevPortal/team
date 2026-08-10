import frappe
from frappe import _

from sriaas_role_permissions.api.field_policy import can_edit_field, get_field_policy
from sriaas_role_permissions.api.roles import is_privileged


TEAM_CHANGE_ERROR = _("Only privileged users can change the Team value.")
TEAM_EDIT_USERS = {"Administrator"}
TEAM_FIELD = "team"
_NO_ALLOWED_TEAM = object()


def can_edit_team(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user in TEAM_EDIT_USERS:
		return True

	return bool(is_privileged(user, "CRM Lead"))


def can_view_team(user: str | None = None) -> bool:
	user = user or frappe.session.user
	return user not in {"", "Guest"}


def can_set_team_on_create(ref_doctype: str, user: str | None = None) -> bool:
	user = user or frappe.session.user
	policy = get_field_policy(ref_doctype, TEAM_FIELD, user=user, is_new=True)
	return bool(
		policy.get("can_edit")
		and policy.get("reason") in {"privileged", "leaders_can_set_when_creating", "leaders_can_change"}
	)


def can_change_team(ref_doctype: str, user: str | None = None) -> bool:
	user = user or frappe.session.user
	return can_edit_field(ref_doctype, TEAM_FIELD, user=user, is_new=False)


def can_change_team_for_doc(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if can_edit_team(user):
		return True
	return bool(can_change_team(doc.doctype, user) or (doc.is_new() and can_set_team_on_create(doc.doctype, user)))


def validate_team_change(doc, allowed_team: str | None | object = _NO_ALLOWED_TEAM):
	if can_change_team_for_doc(doc) or not hasattr(doc, "team"):
		return

	previous_team = None
	if not doc.is_new():
		previous_team = frappe.db.get_value(doc.doctype, doc.name, "team")

	if previous_team != doc.team:
		if allowed_team is not _NO_ALLOWED_TEAM and doc.team == allowed_team:
			return

		frappe.throw(TEAM_CHANGE_ERROR)
