const teamFieldReadOnlyForNonAdmin = {
	refresh(frm) {
		if (!frm.fields_dict.team) {
			return;
		}

		frappe.call({
			method: "team.api.context.get_team_field_context",
			args: { ref_doctype: frm.doctype, is_new: frm.is_new() ? 1 : 0 },
			callback(r) {
				const context = r.message || {};
				frm.set_df_property("team", "hidden", !context.can_view_team);
				frm.set_df_property("team", "read_only", !context.can_edit_team);
			},
		});
	},
};

frappe.ui.form.on("Patient Encounter", teamFieldReadOnlyForNonAdmin);
frappe.ui.form.on("CRM Deal", teamFieldReadOnlyForNonAdmin);
