const bmd_form_doctypes = [
	"BMD Account",
	"BMD Account Mapping",
	"BMD Dimension Mapping",
	"BMD Export Batch",
	"BMD Export Batch Item",
	"BMD Export Profile",
	"BMD Export Settings",
	"BMD Party Mapping",
	"BMD Tax Mapping",
];

function apply_bmd_form_style(frm) {
	if (!frm.page?.wrapper) return;
	frm.page.wrapper.addClass("bmd-modern-form");
	frm.page.wrapper.attr("data-bmd-doctype", frappe.scrub(frm.doctype));

	if (!frm.__bmd_help_menu_added) {
		frm.page.add_menu_item(__("BMD Export Help"), () => frappe.set_route("bmd-export-help"));
		frm.__bmd_help_menu_added = true;
	}
}

bmd_form_doctypes.forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		setup(frm) {
			apply_bmd_form_style(frm);
		},
		refresh(frm) {
			apply_bmd_form_style(frm);
		},
	});
});
