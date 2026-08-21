frappe.pages["bmd-export-assistant"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("BMD Export Assistant"),
		single_column: true,
	});
	page.add_inner_button(__("Help"), () => frappe.set_route("bmd-export-help"));

	const form = $('<div class="frappe-card p-5"></div>').appendTo(page.body);
	$(
		`<p>${__(
			"Create a validated preview first. The export renames only package copies of attachments; ERPNext files remain unchanged."
		)}</p>`
	).appendTo(form);

	const fields = {};
	[
		{
			fieldname: "company",
			fieldtype: "Link",
			options: "Company",
			label: __("Company"),
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		{ fieldname: "from_date", fieldtype: "Date", label: __("From Date"), reqd: 1 },
		{ fieldname: "to_date", fieldtype: "Date", label: __("To Date"), reqd: 1 },
		{
			fieldname: "include_sales_invoices",
			fieldtype: "Check",
			label: __("Sales Invoices"),
			default: 1,
		},
		{
			fieldname: "include_purchase_invoices",
			fieldtype: "Check",
			label: __("Purchase Invoices"),
			default: 1,
		},
	].forEach((definition) => {
		const control = frappe.ui.form.make_control({ df: definition, parent: form, render_input: true });
		control.set_value(definition.default || "");
		fields[definition.fieldname] = control;
	});

	const button = $(
		`<button class="btn btn-primary mt-4">${__("Create Preview")}</button>`
	).appendTo(form);
	button.on("click", async () => {
		const args = Object.fromEntries(
			Object.entries(fields).map(([fieldname, control]) => [fieldname, control.get_value()])
		);
		if (!args.company || !args.from_date || !args.to_date) {
			frappe.msgprint(__("Company and date range are required."));
			return;
		}
		button.prop("disabled", true);
		try {
			const response = await frappe.call({
				method: "kmu_erp_austria.bmd_export.api.create_preview",
				args,
				freeze: true,
				freeze_message: __("Validating BMD export..."),
			});
			frappe.set_route("Form", "BMD Export Batch", response.message.batch);
		} finally {
			button.prop("disabled", false);
		}
	});
};
