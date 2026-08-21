frappe.query_reports["BMD Missing Mappings"] = {
	filters: [
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
			fieldname: "voucher_type",
			fieldtype: "Select",
			label: __("Voucher Type"),
			options: "\nSales Invoice\nPurchase Invoice",
		},
	],
};
