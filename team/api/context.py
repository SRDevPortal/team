from __future__ import annotations

import frappe

from team.api.team_permissions import can_change_team, can_edit_team, can_set_team_on_create, can_view_team


@frappe.whitelist()
def get_team_field_context(ref_doctype: str | None = None, is_new: bool | int | str = False) -> dict:
	user = frappe.session.user
	ref_doctype = ref_doctype or "CRM Lead"
	is_new = str(is_new).lower() in {"1", "true", "yes"}
	can_edit = can_edit_team(user)
	can_change = can_change_team(ref_doctype, user)
	can_set_on_create = can_set_team_on_create(ref_doctype, user)
	field_policy = {}
	try:
		from sriaas_role_permissions.api.field_policy import get_field_policy

		field_policy = get_field_policy(ref_doctype, "team", user=user, is_new=is_new)
	except Exception:
		field_policy = {}
	context = {
		"user": user,
		"ref_doctype": ref_doctype,
		"can_view_team": can_view_team(user),
		"can_edit_team": bool(can_edit or can_change or (is_new and can_set_on_create)),
		"can_change_team": bool(can_change),
		"can_set_team_on_create": bool(can_set_on_create),
		"field_policy": field_policy,
		"is_privileged": False,
		"has_team_leader_role": False,
		"has_agent_role": False,
	}

	try:
		from sriaas_role_permissions.api.roles import (
			has_agent_role,
			has_team_leader_role,
			is_privileged,
		)

		context.update(
			{
				"ref_doctype": ref_doctype,
				"is_privileged": bool(is_privileged(user, ref_doctype)),
				"has_team_leader_role": bool(has_team_leader_role(user, ref_doctype)),
				"has_agent_role": bool(has_agent_role(user, ref_doctype)),
			}
		)
	except Exception:
		context["is_privileged"] = context["can_edit_team"]

	return context
