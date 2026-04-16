import frappe
from frappe import _
from frappe.model.document import Document


class Team(Document):
	def validate(self):
		self.validate_members()
		self.validate_team_lead()

	def validate_members(self):
		seen_users = set()

		for row in self.members or []:
			if not row.user:
				continue

			if row.user in seen_users:
				frappe.throw(_("User {0} is duplicated in members.").format(row.user))

			seen_users.add(row.user)
			self.validate_member_not_in_other_team(row.user)

	def validate_member_not_in_other_team(self, user: str):
		rows = frappe.get_all(
			"Team User",
			filters={
				"user": user,
				"parenttype": "Team",
				"parent": ["!=", self.name or ""],
			},
			fields=["parent"],
			limit=1,
		)
		if rows:
			frappe.throw(_("User {0} is already assigned to team {1}.").format(user, rows[0].parent))

	def validate_team_lead(self):
		if not self.team_lead:
			return

		member_users = {row.user for row in self.members if row.user}
		if self.team_lead not in member_users:
			frappe.throw(_("Team Lead must also be added in Members."))
