frappe.ui.form.on("BMD Export Settings", {
	refresh(frm) {
		frm.add_custom_button(__("BMD Export Help"), () => frappe.set_route("bmd-export-help"));
		if (!frm.is_new()) {
			frm.add_custom_button(__("Test Attachment Filename"), () => {
				frappe.call({
					method: "kmu_erp_austria.bmd_export.api.preview_document_filename",
					args: {
						template: frm.doc.document_filename_template,
						original_filename: "test.pdf",
					},
					callback: (response) =>
						frappe.msgprint({
							title: __("Export Filename Preview"),
							message: response.message,
							indicator: "green",
						}),
				});
			});
		}
	},
});
