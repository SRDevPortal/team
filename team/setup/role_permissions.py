import frappe


SETTINGS_DOCTYPE = "SRIAAS Role Permission Settings"
TEAM_FIELD_DOCTYPES = ("CRM Lead", "CRM Deal", "Patient Encounter")


def apply_role_permission_rules():
	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return

	settings = frappe.get_single(SETTINGS_DOCTYPE)
	existing = {
		(row.ref_doctype, row.fieldname)
		for row in settings.get("locked_fields")
		if row.ref_doctype and row.fieldname
	}
	changed = False

	for ref_doctype in TEAM_FIELD_DOCTYPES:
		if not frappe.db.exists("DocType", ref_doctype) or not frappe.db.has_column(ref_doctype, "team"):
			continue
		if (ref_doctype, "team") in existing:
			continue

		settings.append(
			"locked_fields",
			{
				"enabled": 1,
				"ref_doctype": ref_doctype,
				"fieldname": "team",
				"lock_after_insert": 1,
				"leaders_can_change": 0,
				"agent_always_lock": 1,
			},
		)
		changed = True

	if changed:
		settings.save(ignore_permissions=True)
		frappe.clear_cache(doctype=SETTINGS_DOCTYPE)
