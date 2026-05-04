# Copyright (c) 2026, SRIAAS and Contributors
# See license.txt

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from team.api.team_permissions import TEAM_CHANGE_ERROR
from team.api.team_logic import (
	auto_set_team,
	set_team_for_crm_deal,
	set_team_for_crm_lead,
	set_team_for_patient_encounter,
	update_linked_deals_team,
)
from team.api.team_permissions import validate_team_change


class TestTeam(FrappeTestCase):
	def test_non_admin_cannot_change_team_on_existing_doc(self):
		doc = SimpleNamespace(
			doctype="CRM Lead",
			name="LEAD-0001",
			team="Team B",
			is_new=lambda: False,
		)

		with (
			patch("team.api.team_permissions.can_edit_team", return_value=False),
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

		with patch("team.api.team_permissions.can_edit_team", return_value=False):
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
