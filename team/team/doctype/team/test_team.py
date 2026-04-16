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

	def test_patient_encounter_auto_sets_team_for_user(self):
		doc = SimpleNamespace(team=None, is_new=lambda: True)

		with (
			patch("team.api.team_logic.validate_team_change"),
			patch("team.api.team_logic.frappe.session.user", "test@example.com"),
			patch("team.api.team_logic.get_team_for_user", return_value="Clinical Team"),
		):
			set_team_for_patient_encounter(doc)

		self.assertEqual(doc.team, "Clinical Team")

	def test_crm_lead_auto_sets_team_from_lead_owner(self):
		doc = SimpleNamespace(team=None, lead_owner="owner@example.com", is_new=lambda: True)

		with (
			patch("team.api.team_logic.validate_team_change"),
			patch("team.api.team_logic.get_team_for_user", return_value="Sales Team"),
		):
			set_team_for_crm_lead(doc)

		self.assertEqual(doc.team, "Sales Team")

	def test_crm_deal_auto_sets_team_from_lead(self):
		doc = SimpleNamespace(team=None, lead="LEAD-0001", is_new=lambda: True)

		with (
			patch("team.api.team_logic.validate_team_change"),
			patch("team.api.team_logic.frappe.db.get_value", return_value="Sales Team"),
		):
			set_team_for_crm_deal(doc)

		self.assertEqual(doc.team, "Sales Team")
