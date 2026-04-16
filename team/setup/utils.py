import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

MODULE_DEF_NAME = "Team"
APP_NAME = "team"


def ensure_module_def():
	if frappe.db.exists("Module Def", MODULE_DEF_NAME):
		return

	frappe.get_doc(
		{
			"doctype": "Module Def",
			"module_name": MODULE_DEF_NAME,
			"app_name": APP_NAME,
		}
	).insert(ignore_permissions=True)


def create_cf_with_module(field_map: dict[str, list[dict]]):
	for fields in field_map.values():
		for field in fields:
			field.setdefault("module", MODULE_DEF_NAME)

	create_custom_fields(field_map, ignore_validate=True)
