const teamFieldReadOnlyForNonAdmin = {
	refresh(frm) {
		if (!frm.fields_dict.team) {
			return;
		}

		frm.set_df_property("team", "read_only", frappe.session.user !== "Administrator");
	},
};

frappe.ui.form.on("Patient Encounter", teamFieldReadOnlyForNonAdmin);
frappe.ui.form.on("CRM Lead", teamFieldReadOnlyForNonAdmin);
frappe.ui.form.on("CRM Deal", teamFieldReadOnlyForNonAdmin);
