import frappe

MODULE_NAME = "Team"


def ensure_team_doctypes():
	ensure_team_user_doctype()
	ensure_team_doctype()
	sync_team_permissions()


def ensure_team_user_doctype():
	if frappe.db.exists("DocType", "Team User"):
		return

	frappe.get_doc(
		{
			"doctype": "DocType",
			"name": "Team User",
			"module": MODULE_NAME,
			"istable": 1,
			"editable_grid": 1,
			"custom": 0,
			"engine": "InnoDB",
			"field_order": [
				"user",
				"is_active",
			],
			"fields": [
				{
					"fieldname": "user",
					"label": "User",
					"fieldtype": "Link",
					"options": "User",
					"reqd": 1,
					"in_list_view": 1,
				},
				{
					"fieldname": "is_active",
					"label": "Is Active",
					"fieldtype": "Check",
					"default": "1",
					"in_list_view": 1,
				},
			],
		}
	).insert(ignore_permissions=True)


def ensure_team_doctype():
	if frappe.db.exists("DocType", "Team"):
		return

	frappe.get_doc(
		{
			"doctype": "DocType",
			"name": "Team",
			"module": MODULE_NAME,
			"custom": 0,
			"engine": "InnoDB",
			"track_changes": 1,
			"autoname": "field:team_name",
			"title_field": "team_name",
			"search_fields": "team_name,team_code,team_lead",
			"field_order": [
				"team_name",
				"team_code",
				"team_type",
				"is_active",
				"team_lead",
				"description",
				"members",
			],
			"fields": [
				{
					"fieldname": "team_name",
					"label": "Team Name",
					"fieldtype": "Data",
					"reqd": 1,
					"in_list_view": 1,
				},
				{
					"fieldname": "team_code",
					"label": "Team Code",
					"fieldtype": "Data",
					"unique": 1,
					"in_list_view": 1,
				},
				{
					"fieldname": "team_type",
					"label": "Team Type",
					"fieldtype": "Select",
					"options": "\nClinical\nSales\nSupport\nOperations",
					"in_list_view": 1,
				},
				{
					"fieldname": "is_active",
					"label": "Is Active",
					"fieldtype": "Check",
					"default": "1",
					"in_list_view": 1,
				},
				{
					"fieldname": "team_lead",
					"label": "Team Lead",
					"fieldtype": "Link",
					"options": "User",
					"in_list_view": 1,
				},
				{
					"fieldname": "description",
					"label": "Description",
					"fieldtype": "Small Text",
				},
				{
					"fieldname": "members",
					"label": "Members",
					"fieldtype": "Table",
					"options": "Team User",
					"reqd": 1,
				},
			],
			"permissions": [
				{
					"role": "System Manager",
					"read": 1,
					"write": 1,
					"create": 1,
					"delete": 1,
					"share": 1,
					"export": 1,
					"print": 1,
					"email": 1,
					"report": 1,
				},
				{
					"role": "All",
					"read": 1,
					"report": 1,
				},
			],
		}
	).insert(ignore_permissions=True)


def sync_team_permissions():
	if not frappe.db.exists("DocType", "Team"):
		return

	doc = frappe.get_doc("DocType", "Team")
	doc.set(
		"permissions",
		[
			{
				"role": "System Manager",
				"read": 1,
				"write": 1,
				"create": 1,
				"delete": 1,
				"share": 1,
				"export": 1,
				"print": 1,
				"email": 1,
				"report": 1,
			},
			{
				"role": "All",
				"read": 1,
				"write": 0,
				"create": 0,
				"delete": 0,
				"share": 0,
				"export": 0,
				"print": 0,
				"email": 0,
				"report": 1,
			},
		],
	)
	doc.save(ignore_permissions=True)
