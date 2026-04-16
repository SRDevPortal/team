import frappe
from frappe import _

from .team_permissions import validate_team_change


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


def set_team_for_patient_encounter(doc, method=None):
	if not hasattr(doc, "team"):
		return

	validate_team_change(doc)

	auto_set_team(doc, frappe.session.user)


def set_team_for_crm_lead(doc, method=None):
	if not hasattr(doc, "team"):
		return

	validate_team_change(doc)

	if not doc.lead_owner:
		return

	auto_set_team(doc, doc.lead_owner)


def set_team_for_crm_deal(doc, method=None):
	if not hasattr(doc, "team"):
		return

	validate_team_change(doc)

	if not doc.lead or doc.team:
		return

	doc.team = frappe.db.get_value("CRM Lead", doc.lead, "team")
