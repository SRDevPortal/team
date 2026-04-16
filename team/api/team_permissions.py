import frappe
from frappe import _


TEAM_CHANGE_ERROR = _("Only Administrator can change the Team value.")
TEAM_EDIT_USERS = {"Administrator"}


def can_edit_team(user: str | None = None) -> bool:
	return (user or frappe.session.user) in TEAM_EDIT_USERS


def validate_team_change(doc):
	if can_edit_team() or not hasattr(doc, "team"):
		return

	previous_team = None
	if not doc.is_new():
		previous_team = frappe.db.get_value(doc.doctype, doc.name, "team")

	if previous_team != doc.team:
		frappe.throw(TEAM_CHANGE_ERROR)
