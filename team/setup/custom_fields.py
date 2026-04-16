import frappe

from .utils import create_cf_with_module


def apply_custom_fields():
	field_map = {}

	if frappe.db.exists("DocType", "Patient Encounter"):
		field_map["Patient Encounter"] = [
			{
				"fieldname": "team",
				"label": "Care Team",
				"fieldtype": "Link",
				"options": "Team",
				"insert_after": "practitioner_name",
				"in_list_view": 1,
				"in_standard_filter": 1,
			}
		]

	if frappe.db.exists("DocType", "CRM Lead"):
		field_map["CRM Lead"] = [
			{
				"fieldname": "team",
				"label": "Sales Team",
				"fieldtype": "Link",
				"options": "Team",
				"insert_after": "lead_owner",
				"in_list_view": 1,
				"in_standard_filter": 1,
			}
		]

	if frappe.db.exists("DocType", "CRM Deal"):
		field_map["CRM Deal"] = [
			{
				"fieldname": "team",
				"label": "Sales Team",
				"fieldtype": "Link",
				"options": "Team",
				"insert_after": "deal_owner",
				"in_list_view": 1,
				"in_standard_filter": 1,
			}
		]

	if field_map:
		create_cf_with_module(field_map)
