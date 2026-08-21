frappe.pages["bmd-export-help"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("BMD Export Help"),
		single_column: true,
	});

	page.set_primary_action(__("Open Export Assistant"), () =>
		frappe.set_route("bmd-export-assistant")
	);
	page.add_menu_item(__("BMD Export Settings"), () =>
		frappe.set_route("List", "BMD Export Settings")
	);
	page.add_menu_item(__("Missing Mappings"), () =>
		frappe.set_route("query-report", "BMD Missing Mappings")
	);

	const chapters = [
		["overview", __("Overview")],
		["setup", __("Initial Setup")],
		["mappings", __("Mappings")],
		["filenames", __("Attachment Filenames")],
		["export", __("Run Export")],
		["bmd-import", __("Import into BMD")],
		["errors", __("Troubleshooting")],
	];

	const content = $(
		`<div class="bmd-help">
			<nav class="bmd-help-nav frappe-card" aria-label="${__("BMD Help Chapters")}">
				<div class="bmd-help-nav-title">${__("Chapters")}</div>
				<div class="bmd-help-nav-links"></div>
			</nav>
			<main class="bmd-help-content">
				<section id="overview" class="frappe-card">
					<h2>${__("Overview")}</h2>
					<p>${__("The BMD Export module creates a BMD-compatible buchungen.csv from submitted Sales and Purchase Invoices. A flat ZIP contains the CSV and all referenced documents.")}</p>
					<div class="alert alert-info">${__("The ZIP is a transport package. Unzip it before importing and select only buchungen.csv in BMD NTCS.")}</div>
				</section>
				<section id="setup" class="frappe-card">
					<h2>${__("Initial Setup")}</h2>
					<ol>
						<li>${__("Assign BMD Export User or BMD Export Manager to the users involved.")}</li>
						<li>${__("Create one BMD Export Settings record for each Company and select an active export profile.")}</li>
						<li>${__("Import the BMD chart of accounts from the BMD Account list using Import XLSX/CSV.")}</li>
						<li>${__("Create the required account, party, tax and dimension mappings.")}</li>
						<li>${__("Use the Missing Mappings report before the first export.")}</li>
					</ol>
					<div class="bmd-help-actions">
						<button class="btn btn-default" data-route="List/BMD Export Settings">${__("Open Settings")}</button>
						<button class="btn btn-default" data-route="List/BMD Account">${__("Open BMD Accounts")}</button>
					</div>
				</section>
				<section id="mappings" class="frappe-card">
					<h2>${__("Mappings")}</h2>
					<p>${__("Every exported target value must be resolved unambiguously for the Company and posting date. Missing or equally ranked mappings block the preview.")}</p>
					<ul>
						<li><b>${__("Account Mapping")}:</b> ${__("ERPNext income or expense account to BMD general-ledger account.")}</li>
						<li><b>${__("Party Mapping")}:</b> ${__("Customer or Supplier to BMD person account.")}</li>
						<li><b>${__("Tax Mapping")}:</b> ${__("Direction, rate, BMD tax code, amount source, sign rule, branch and OSS values.")}</li>
						<li><b>${__("Dimension Mapping")}:</b> ${__("Cost Center, Project or Accounting Dimension to a BMD KORE field.")}</li>
					</ul>
					<p>${__("Identical account numbers are never treated as an automatic mapping.")}</p>
					<div class="bmd-help-actions">
						<button class="btn btn-default" data-route="List/BMD Account Mapping">${__("Account Mappings")}</button>
						<button class="btn btn-default" data-route="List/BMD Party Mapping">${__("Party Mappings")}</button>
						<button class="btn btn-default" data-route="List/BMD Tax Mapping">${__("Tax Mappings")}</button>
						<button class="btn btn-default" data-route="List/BMD Dimension Mapping">${__("Dimension Mappings")}</button>
					</div>
				</section>
				<section id="filenames" class="frappe-card">
					<h2>${__("Attachment Filenames")}</h2>
					<p>${__("The Jinja template in BMD Export Settings is applied to every exported attachment. Only the package copy is renamed; the original ERPNext File remains unchanged.")}</p>
					<pre><code>{{ invoice_number }}-{{ party_name }}</code></pre>
					<p>${__("Example: test.pdf becomes AR-2026-0042-Musterkunde.pdf. The verified source extension is appended automatically.")}</p>
					<p><b>${__("Available variables")}:</b> company, voucher_type, voucher_type_code, voucher_name, invoice_number, external_invoice_number, bill_no, posting_date_yyyymmdd, party, party_name, return_against, attachment_no, original_stem, extension.</p>
					<p>${__("Use Test Attachment Filename in the settings form to preview the final name.")}</p>
				</section>
				<section id="export" class="frappe-card">
					<h2>${__("Run Export")}</h2>
					<ol>
						<li>${__("Open the BMD Export Assistant and select Company, date range and invoice types.")}</li>
						<li>${__("Create the preview and inspect Batch Items, totals, final document names, errors and warnings.")}</li>
						<li>${__("Resolve all blocking errors and refresh the preview until the batch is Ready.")}</li>
						<li>${__("Select Generate Export. The background job verifies all fingerprints again.")}</li>
						<li>${__("Download the private CSV or ZIP after the batch reaches Completed.")}</li>
					</ol>
					<button class="btn btn-primary" data-page="bmd-export-assistant">${__("Open Export Assistant")}</button>
				</section>
				<section id="bmd-import" class="frappe-card">
					<h2>${__("Import into BMD NTCS")}</h2>
					<ol>
						<li>${__("Download the completed transport ZIP.")}</li>
						<li>${__("Unzip CSV and documents into the same folder.")}</li>
						<li>${__("Start the booking import in BMD NTCS and select only buchungen.csv.")}</li>
						<li>${__("Check booking symbols, tax codes, split groups, KORE rows, totals and document links in the BMD preview.")}</li>
					</ol>
				</section>
				<section id="errors" class="frappe-card">
					<h2>${__("Troubleshooting")}</h2>
					<ul>
						<li><code>MISSING_MAPPING</code>: ${__("Create a valid mapping for the Company and posting date.")}</li>
						<li><code>AMBIGUOUS_MAPPING</code>: ${__("Remove an overlap or assign a unique priority.")}</li>
						<li><code>ATTACHMENT_*</code>: ${__("Check requirement, file size, extension, MIME type and readability.")}</li>
						<li><code>ENCODING_ERROR</code>: ${__("Choose UTF-8 or change characters that cannot be represented by CP1252.")}</li>
						<li><code>*_RECONCILIATION_FAILED</code>: ${__("Check invoice totals, item tax details, mapping amount sources and GL entries.")}</li>
					</ul>
					<p>${__("A failed batch can be validated again. A completed batch is immutable; managers create a separate re-export revision.")}</p>
				</section>
			</main>
		</div>`
	).appendTo(page.body);

	const links = content.find(".bmd-help-nav-links");
	chapters.forEach(([id, label], index) => {
		$(`<a href="#${id}" class="bmd-help-nav-link ${index === 0 ? "active" : ""}">${label}</a>`)
			.appendTo(links)
			.on("click", function (event) {
				event.preventDefault();
				content.find(".bmd-help-nav-link").removeClass("active");
				$(this).addClass("active");
				content.find(`#${id}`)[0].scrollIntoView({ behavior: "smooth", block: "start" });
				history.replaceState(null, "", `#${id}`);
			});
	});

	content.on("click", "[data-route]", function () {
		const [view, doctype] = $(this).data("route").split("/");
		frappe.set_route(view, doctype);
	});
	content.on("click", "[data-page]", function () {
		frappe.set_route($(this).data("page"));
	});

	const selected = window.location.hash.slice(1);
	if (chapters.some(([id]) => id === selected)) {
		setTimeout(() => content.find(`.bmd-help-nav-link[href="#${selected}"]`).trigger("click"), 0);
	}
};
