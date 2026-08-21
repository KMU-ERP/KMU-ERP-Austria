frappe.ui.form.on("BMD Export Batch", {
	refresh(frm) {
		frm.add_custom_button(__("BMD Export Help"), () => frappe.set_route("bmd-export-help"));
		if (["Invalid", "Ready", "Failed"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Refresh Preview"), () =>
				frappe.call({
					method: "kmu_erp_austria.bmd_export.api.refresh_preview",
					args: { batch_name: frm.doc.name },
					freeze: true,
					callback: () => frm.reload_doc(),
				})
			);
		}
		if (frm.doc.status === "Ready") {
			frm.add_custom_button(__("Generate Export"), () =>
				frappe.call({
					method: "kmu_erp_austria.bmd_export.api.start_export",
					args: { batch_name: frm.doc.name },
					freeze: true,
					callback: () => frm.reload_doc(),
				})
			).addClass("btn-primary");
		}
		if (
			["Completed", "Superseded"].includes(frm.doc.status) &&
			(frappe.user.has_role("BMD Export Manager") || frappe.user.has_role("System Manager"))
		) {
			frm.add_custom_button(__("Create Re-export"), () =>
				frappe.call({
					method: "kmu_erp_austria.bmd_export.api.create_reexport",
					args: { batch_name: frm.doc.name },
					freeze: true,
					callback: (response) =>
						frappe.set_route("Form", "BMD Export Batch", response.message.batch),
				})
			);
		}
		if (frm.doc.status === "Completed") {
			frm.dashboard.set_headline(
				__("BMD import: unzip the transport package, then select only buchungen.csv in NTCS.")
			);
		}
		frappe.realtime.off("bmd_export_progress");
		frappe.realtime.on("bmd_export_progress", (data) => {
			if (data.batch !== frm.doc.name) return;
			frm.doc.progress = data.progress;
			frm.refresh_field("progress");
			if (data.status !== frm.doc.status) frm.reload_doc();
		});
	},
});
