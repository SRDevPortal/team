import frappe
from frappe import _

from .team_permissions import can_edit_team, validate_team_change


def get_team_for_user(user: str | None) -> str | None:
	if not user or user == "Guest":
		return None

	rows = frappe.db.sql(
		"""
		select tu.parent
		from `tabTeam User` tu
		inner join `tabTeam` t on t.name = tu.parent
		where tu.user = %s
		  and ifnull(tu.is_active, 1) = 1
		  and ifnull(t.is_active, 1) = 1
		limit 2
		""",
		(user,),
		as_dict=True,
	)

	if not rows:
		return None

	if len(rows) > 1:
		frappe.throw(_("User {0} is linked with more than one active team.").format(user))

	return rows[0].parent


def auto_set_team(doc, user: str | None):
	if not hasattr(doc, "team") or doc.team:
		return

	doc.team = get_team_for_user(user)


def get_previous_value(doc, fieldname: str):
	if doc.is_new():
		return None

	if hasattr(doc, "has_value_changed") and not doc.has_value_changed(fieldname):
		return doc.get(fieldname)

	return frappe.db.get_value(doc.doctype, doc.name, fieldname)


def has_value_changed(doc, fieldname: str) -> bool:
	if doc.is_new():
		return True

	if hasattr(doc, "has_value_changed"):
		return doc.has_value_changed(fieldname)

	return get_previous_value(doc, fieldname) != getattr(doc, fieldname, None)


def apply_system_team(doc, team: str | None, force: bool = False):
	validate_team_change(doc, allowed_team=team)

	if force or not doc.team or not can_edit_team():
		doc.team = team


def set_team_for_patient_encounter(doc, method=None):
	if not hasattr(doc, "team"):
		return

	team = get_team_for_user(doc.owner)
	apply_system_team(doc, team, force=doc.is_new() or not doc.team)


def set_team_for_crm_lead(doc, method=None):
	if not hasattr(doc, "team"):
		return

	team = get_team_for_user(doc.lead_owner) if doc.lead_owner else None
	lead_owner_changed = has_value_changed(doc, "lead_owner")

	apply_system_team(doc, team, force=lead_owner_changed or not doc.team)


def set_team_for_crm_deal(doc, method=None):
	if not hasattr(doc, "team"):
		return

	team = frappe.db.get_value("CRM Lead", doc.lead, "team") if doc.lead else None
	lead_changed = has_value_changed(doc, "lead")

	apply_system_team(doc, team, force=lead_changed or not doc.team)


def update_linked_deals_team(doc, method=None):
	if not hasattr(doc, "team") or doc.is_new() or not has_value_changed(doc, "team"):
		return

	for deal in frappe.get_all("CRM Deal", filters={"lead": doc.name}, pluck="name"):
		frappe.db.set_value("CRM Deal", deal, "team", doc.team, update_modified=False)
