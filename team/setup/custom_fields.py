import json

import frappe

from .utils import create_cf_with_module


def apply_custom_fields():
	field_map = {}

	if frappe.db.exists("DocType", "Patient Encounter"):
		field_map["Patient Encounter"] = [
			{
				"fieldname": "team",
				"label": "Sales Team",
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
		apply_crm_field_layouts()


def apply_crm_field_layouts():
	if not frappe.db.exists("DocType", "CRM Fields Layout"):
		return

	_update_layout("CRM Lead", "Quick Entry", "team", "lead_owner")
	_update_layout("CRM Lead", "Side Panel", "team", "lead_owner")
	_update_layout("CRM Lead", "Data Fields", "team", "lead_owner")
	_update_layout("CRM Deal", "Quick Entry", "team", "deal_owner")
	_update_layout("CRM Deal", "Side Panel", "team", "deal_owner")
	_update_layout("CRM Deal", "Data Fields", "team", "deal_owner")


def _update_layout(doctype: str, layout_type: str, fieldname: str, insert_after: str):
	name = frappe.db.get_value("CRM Fields Layout", {"dt": doctype, "type": layout_type}, "name")
	if not name:
		return

	raw_layout = frappe.db.get_value("CRM Fields Layout", name, "layout")
	if not raw_layout:
		return

	try:
		layout = json.loads(raw_layout)
	except Exception:
		return

	if _layout_has_field(layout, fieldname):
		return

	if not _insert_field_after(layout, fieldname, insert_after):
		_append_field_to_first_column(layout, fieldname)

	frappe.db.set_value("CRM Fields Layout", name, "layout", json.dumps(layout), update_modified=False)


def _layout_has_field(node, fieldname: str) -> bool:
	if isinstance(node, dict):
		fields = node.get("fields")
		if isinstance(fields, list) and fieldname in fields:
			return True
		return any(_layout_has_field(value, fieldname) for value in node.values())
	if isinstance(node, list):
		return any(_layout_has_field(value, fieldname) for value in node)
	return False


def _insert_field_after(node, fieldname: str, insert_after: str) -> bool:
	if isinstance(node, dict):
		fields = node.get("fields")
		if isinstance(fields, list) and insert_after in fields:
			fields.insert(fields.index(insert_after) + 1, fieldname)
			return True
		return any(_insert_field_after(value, fieldname, insert_after) for value in node.values())
	if isinstance(node, list):
		return any(_insert_field_after(value, fieldname, insert_after) for value in node)
	return False


def _append_field_to_first_column(node, fieldname: str) -> bool:
	if isinstance(node, dict):
		fields = node.get("fields")
		if isinstance(fields, list):
			fields.append(fieldname)
			return True
		return any(_append_field_to_first_column(value, fieldname) for value in node.values())
	if isinstance(node, list):
		return any(_append_field_to_first_column(value, fieldname) for value in node)
	return False
