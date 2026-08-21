frappe.listview_settings["BMD Account"] = {
	onload(listview) {
		if (!(frappe.user.has_role("BMD Export Manager") || frappe.user.has_role("System Manager"))) {
			return;
		}
		listview.page.add_inner_button(__("Import XLSX/CSV"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("Import BMD Accounts"),
				fields: [
					{
						fieldname: "company",
						fieldtype: "Link",
						options: "Company",
						label: __("Company"),
						reqd: 1,
						default: frappe.defaults.get_user_default("Company"),
					},
					{ fieldname: "source", fieldtype: "Data", label: __("Source") },
				],
				primary_action_label: __("Select File and Preview"),
				primary_action(values) {
					new frappe.ui.FileUploader({
						allow_multiple: false,
						restrictions: { allowed_file_types: [".xlsx", ".csv"] },
						on_success(file) {
							frappe.call({
								method: "kmu_erp_austria.bmd_export.api.preview_account_import",
								args: { company: values.company, file_url: file.file_url },
								freeze: true,
								callback(response) {
									const rows = response.message || [];
									const invalid = rows.filter((row) => row.status === "Invalid");
									const summary = `${rows.length} ${__("rows")}, ${invalid.length} ${__("invalid")}`;
									frappe.confirm(summary, () => {
										if (invalid.length) return;
										frappe.call({
											method: "kmu_erp_austria.bmd_export.api.import_accounts",
											args: {
												company: values.company,
												file_url: file.file_url,
												source: values.source,
											},
											freeze: true,
											callback: () => listview.refresh(),
										});
									});
								},
							});
						},
					});
				},
			});
			dialog.show();
		});
	},
};
