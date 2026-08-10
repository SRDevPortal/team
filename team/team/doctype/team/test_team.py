# Copyright (c) 2026, SRIAAS and Contributors
# See license.txt

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from team.api.team_logic import (
	auto_set_team,
	get_team_for_user,
	set_team_for_crm_deal,
	set_team_for_crm_lead,
	set_team_for_patient_encounter,
	update_linked_deals_team,
)
from team.api.team_permissions import (
	TEAM_CHANGE_ERROR,
	can_change_team,
	can_set_team_on_create,
	validate_team_change,
)
from team.setup.role_permissions import TEAM_FIELD_DOCTYPES, apply_role_permission_rules


class TestTeam(FrappeTestCase):
	def make_user(self):
		email = f"team-test-{frappe.generate_hash(length=8)}@example.com"
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Team Test",
				"enabled": 1,
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
		return email

	def make_team(self, user, *, team_lead=None, is_active=1):
		team_name = f"Test Team {frappe.generate_hash(length=8)}"
		return frappe.get_doc(
			{
				"doctype": "Team",
				"team_name": team_name,
				"team_code": frappe.generate_hash(length=8).upper(),
				"is_active": is_active,
				"team_lead": team_lead,
				"members": [{"user": user, "is_active": 1}],
			}
		).insert(ignore_permissions=True)

	def test_non_admin_cannot_change_team_on_existing_doc(self):
		doc = SimpleNamespace(
			doctype="CRM Lead",
			name="LEAD-0001",
			team="Team B",
			is_new=lambda: False,
		)

		with (
			patch("team.api.team_permissions.can_change_team_for_doc", return_value=False),
			patch("team.api.team_permissions.frappe.db.get_value", return_value="Team A"),
		):
			self.assertRaisesRegex(
				frappe.ValidationError,
				TEAM_CHANGE_ERROR,
				validate_team_change,
				doc,
			)

	def test_non_admin_cannot_import_team_on_new_doc(self):
		doc = SimpleNamespace(
			doctype="CRM Lead",
			name=None,
			team="Team A",
			is_new=lambda: True,
		)

		with patch("team.api.team_permissions.can_change_team_for_doc", return_value=False):
			self.assertRaisesRegex(
				frappe.ValidationError,
				TEAM_CHANGE_ERROR,
				validate_team_change,
				doc,
			)

	def test_auto_set_team_only_when_field_is_empty(self):
		doc = SimpleNamespace(team=None)
		with patch("team.api.team_logic.get_team_for_user", return_value="Sales Team"):
			auto_set_team(doc, "test@example.com")
		self.assertEqual(doc.team, "Sales Team")

		with patch("team.api.team_logic.get_team_for_user", return_value="Other Team") as mocked:
			auto_set_team(doc, "test@example.com")
		mocked.assert_not_called()
		self.assertEqual(doc.team, "Sales Team")

	def test_patient_encounter_auto_sets_team_from_creator(self):
		doc = SimpleNamespace(team=None, owner="creator@example.com", is_new=lambda: True)

		with (
			patch("team.api.team_logic.validate_team_change"),
			patch("team.api.team_logic.get_team_for_user", return_value="Clinical Team") as mocked_get_team,
		):
			set_team_for_patient_encounter(doc)

		mocked_get_team.assert_called_once_with("creator@example.com")
		self.assertEqual(doc.team, "Clinical Team")

	def test_crm_lead_auto_sets_team_from_lead_owner_on_create(self):
		doc = SimpleNamespace(team=None, lead_owner="owner@example.com", is_new=lambda: True)

		with (
			patch("team.api.team_logic.validate_team_change"),
			patch("team.api.team_logic.get_team_for_user", return_value="Sales Team"),
		):
			set_team_for_crm_lead(doc)

		self.assertEqual(doc.team, "Sales Team")

	def test_crm_lead_updates_team_when_lead_owner_changes(self):
		doc = SimpleNamespace(
			doctype="CRM Lead",
			name="LEAD-0001",
			team="Paralysis Team",
			lead_owner="sachin@example.com",
			is_new=lambda: False,
			has_value_changed=lambda fieldname: fieldname == "lead_owner",
		)

		with (
			patch("team.api.team_logic.can_edit_team", return_value=False),
			patch("team.api.team_logic.validate_team_change"),
			patch("team.api.team_logic.get_team_for_user", return_value="Parkinson Team"),
		):
			set_team_for_crm_lead(doc)

		self.assertEqual(doc.team, "Parkinson Team")

	def test_crm_lead_clears_team_when_reassigned_user_has_no_team(self):
		doc = SimpleNamespace(
			doctype="CRM Lead",
			name="LEAD-0001",
			team="Paralysis Team",
			lead_owner="sachin@example.com",
			is_new=lambda: False,
			has_value_changed=lambda fieldname: fieldname == "lead_owner",
		)

		with (
			patch("team.api.team_logic.can_edit_team", return_value=False),
			patch("team.api.team_logic.validate_team_change"),
			patch("team.api.team_logic.get_team_for_user", return_value=None),
		):
			set_team_for_crm_lead(doc)

		self.assertIsNone(doc.team)

	def test_crm_deal_auto_sets_team_from_lead(self):
		doc = SimpleNamespace(team=None, lead="LEAD-0001", is_new=lambda: True)

		with (
			patch("team.api.team_logic.validate_team_change"),
			patch("team.api.team_logic.frappe.db.get_value", return_value="Sales Team"),
		):
			set_team_for_crm_deal(doc)

		self.assertEqual(doc.team, "Sales Team")

	def test_crm_deal_updates_team_when_lead_changes(self):
		doc = SimpleNamespace(
			doctype="CRM Deal",
			name="DEAL-0001",
			team="Paralysis Team",
			lead="LEAD-0002",
			is_new=lambda: False,
			has_value_changed=lambda fieldname: fieldname == "lead",
		)

		with (
			patch("team.api.team_logic.can_edit_team", return_value=False),
			patch("team.api.team_logic.validate_team_change"),
			patch("team.api.team_logic.frappe.db.get_value", return_value="Parkinson Team"),
		):
			set_team_for_crm_deal(doc)

		self.assertEqual(doc.team, "Parkinson Team")

	def test_crm_lead_team_change_updates_linked_deals(self):
		doc = SimpleNamespace(
			name="LEAD-0001",
			team="Parkinson Team",
			is_new=lambda: False,
			has_value_changed=lambda fieldname: fieldname == "team",
		)

		with (
			patch("team.api.team_logic.frappe.get_all", return_value=["DEAL-0001", "DEAL-0002"]) as mocked_get_all,
			patch("team.api.team_logic.frappe.db.set_value") as mocked_set_value,
		):
			update_linked_deals_team(doc)

		mocked_get_all.assert_called_once_with("CRM Deal", filters={"lead": "LEAD-0001"}, pluck="name")
		mocked_set_value.assert_any_call("CRM Deal", "DEAL-0001", "team", "Parkinson Team", update_modified=False)
		mocked_set_value.assert_any_call("CRM Deal", "DEAL-0002", "team", "Parkinson Team", update_modified=False)

	def test_change_permission_uses_role_policy(self):
		with patch("team.api.team_permissions.can_edit_field", return_value=False) as mocked:
			self.assertIs(can_change_team("CRM Lead", "agent@example.com"), False)

		mocked.assert_called_once_with("CRM Lead", "team", user="agent@example.com", is_new=False)

	def test_create_permission_requires_an_allowed_policy_reason(self):
		with patch(
			"team.api.team_permissions.get_field_policy",
			return_value={"can_edit": True, "reason": "no_field_rule"},
		):
			self.assertIs(can_set_team_on_create("CRM Lead", "user@example.com"), False)

		with patch(
			"team.api.team_permissions.get_field_policy",
			return_value={"can_edit": True, "reason": "leaders_can_set_when_creating"},
		):
			self.assertIs(can_set_team_on_create("CRM Lead", "leader@example.com"), True)

	def test_team_permission_rules_are_idempotent(self):
		apply_role_permission_rules()
		apply_role_permission_rules()

		settings = frappe.get_single("SRIAAS Role Permission Settings")
		rows = [
			row
			for row in settings.get("locked_fields")
			if row.fieldname == "team" and row.ref_doctype in TEAM_FIELD_DOCTYPES
		]
		configured_doctypes = {
			ref_doctype
			for ref_doctype in TEAM_FIELD_DOCTYPES
			if frappe.db.exists("DocType", ref_doctype) and frappe.db.has_column(ref_doctype, "team")
		}

		self.assertEqual({row.ref_doctype for row in rows}, configured_doctypes)
		self.assertEqual(len(rows), len(configured_doctypes))
		for row in rows:
			self.assertEqual(row.enabled, 1)
			self.assertEqual(row.lock_after_insert, 1)
			self.assertEqual(row.leaders_can_change, 0)
			self.assertEqual(row.agent_always_lock, 1)

	def test_user_cannot_belong_to_two_teams(self):
		user = self.make_user()
		self.make_team(user)

		with self.assertRaisesRegex(frappe.ValidationError, "already assigned to team"):
			self.make_team(user)

	def test_duplicate_member_in_same_team_is_rejected(self):
		user = self.make_user()
		team = frappe.get_doc(
			{
				"doctype": "Team",
				"team_name": f"Test Team {frappe.generate_hash(length=8)}",
				"members": [
					{"user": user, "is_active": 1},
					{"user": user, "is_active": 1},
				],
			}
		)

		with self.assertRaisesRegex(frappe.ValidationError, "duplicated in members"):
			team.insert(ignore_permissions=True)

	def test_team_lead_must_be_a_member(self):
		member = self.make_user()
		team_lead = self.make_user()

		with self.assertRaisesRegex(frappe.ValidationError, "Team Lead must also be added"):
			self.make_team(member, team_lead=team_lead)

	def test_active_team_lookup(self):
		user = self.make_user()
		team = self.make_team(user)

		self.assertEqual(get_team_for_user(user), team.name)
		self.assertIsNone(get_team_for_user("Guest"))

	def test_team_custom_fields_and_user_index_exist(self):
		for doctype in TEAM_FIELD_DOCTYPES:
			field = frappe.get_meta(doctype).get_field("team")
			self.assertTrue(field)
			self.assertEqual(field.fieldtype, "Link")
			self.assertEqual(field.options, "Team")

		user_field = frappe.get_meta("Team User").get_field("user")
		self.assertEqual(user_field.search_index, 1)
