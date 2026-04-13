app_name = "kmu_erp_austria"
app_title = "Kmu Erp Austria"
app_publisher = "RAN Soft GmbH & Co KG"
app_description = "Frappe app with austrian default settings"
app_email = "office@ransoft.at"
app_license = "mit"


# Fixtures

fixtures = [
	{"dt": "Print Format", "filters": [["name", "in", ["Angebot - KMU ERP Austria", "Auftragsbestätigung - KMU ERP Austria",  "Lieferschein - KMU ERP Austria", "Ausgangsrechnung - KMU ERP Austria"]]]},
	"Item Group",
	"Tax Category"
]



# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "kmu_erp_austria",
# 		"logo": "/assets/kmu_erp_austria/logo.png",
# 		"title": "Kmu Erp Austria",
# 		"route": "/kmu_erp_austria",
# 		"has_permission": "kmu_erp_austria.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kmu_erp_austria/css/kmu_erp_austria.css"
# app_include_js = "/assets/kmu_erp_austria/js/kmu_erp_austria.js"

# include js, css files in header of web template
# web_include_css = "/assets/kmu_erp_austria/css/kmu_erp_austria.css"
# web_include_js = "/assets/kmu_erp_austria/js/kmu_erp_austria.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kmu_erp_austria/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kmu_erp_austria/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "kmu_erp_austria.utils.jinja_methods",
# 	"filters": "kmu_erp_austria.utils.jinja_filters"
# }

# Installation
# ------------

before_install = "kmu_erp_austria.install.before_install"
after_install = "kmu_erp_austria.install.after_install"
after_sync = ["kmu_erp_austria.install.after_sync"]
after_migrate = ["kmu_erp_austria.install.after_migrate"]

# Uninstallation
# ------------

# before_uninstall = "kmu_erp_austria.uninstall.before_uninstall"
# after_uninstall = "kmu_erp_austria.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kmu_erp_austria.utils.before_app_install"
# after_app_install = "kmu_erp_austria.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kmu_erp_austria.utils.before_app_uninstall"
# after_app_uninstall = "kmu_erp_austria.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kmu_erp_austria.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
 	"Company": {
 		"on_update": "kmu_erp_austria.setup.letter_head.on_company_update"
 	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"kmu_erp_austria.tasks.all"
# 	],
# 	"daily": [
# 		"kmu_erp_austria.tasks.daily"
# 	],
# 	"hourly": [
# 		"kmu_erp_austria.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kmu_erp_austria.tasks.weekly"
# 	],
# 	"monthly": [
# 		"kmu_erp_austria.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "kmu_erp_austria.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "kmu_erp_austria.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kmu_erp_austria.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kmu_erp_austria.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kmu_erp_austria.utils.before_request"]
# after_request = ["kmu_erp_austria.utils.after_request"]

# Job Events
# ----------
# before_job = ["kmu_erp_austria.utils.before_job"]
# after_job = ["kmu_erp_austria.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"kmu_erp_austria.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

