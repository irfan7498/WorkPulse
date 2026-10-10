app_name = "workpulse"
app_title = "WorkPulse"
app_publisher = "WorkPulse"
app_description = "AI-powered workforce and project intelligence for ERPNext"
app_email = "irfanpathan1045@gmail.com"
app_license = "mit"

required_apps = ["frappe", "erpnext", "hrms"]

doc_events = {
	"Task": {
		"validate": "workpulse.tasks.events.mark_task_health",
		"on_update": "workpulse.tasks.events.queue_task_snapshot",
	},
	"Leave Application": {
		"after_insert": "workpulse.leave_impact.events.on_leave_saved",
		"on_update": "workpulse.leave_impact.events.on_leave_saved",
	}
}

scheduler_events = {
	"daily": [
		"workpulse.tasks.snapshots.enqueue_nightly_workload",
		"workpulse.tasks.project_snapshots.enqueue_daily_project_snapshots",
	],
	"weekly": ["workpulse.tasks.history.enqueue_history_build"],
}

doctype_js = {
	"Leave Application": "public/js/leave_application.js",
	"Task": "public/js/task.js",
	"WP Allocation Recommendation": "public/js/wp_allocation_recommendation.js",
	"Leave Impact Analysis": "public/js/leave_impact_analysis.js",
}

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "workpulse",
		"logo": "/assets/workpulse/logo.png",
		"title": "WorkPulse",
		"route": "/app/workpulse",
		"has_permission": "workpulse.api.permission.has_app_permission"
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/workpulse/css/workpulse.css?v=2"
# app_include_js = "/assets/workpulse/js/workpulse.js"

# include js, css files in header of web template
# web_include_css = "/assets/workpulse/css/workpulse.css"
# web_include_js = "/assets/workpulse/js/workpulse.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "workpulse/public/scss/website"

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
# app_include_icons = "workpulse/public/icons.svg"

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
# 	"methods": "workpulse.utils.jinja_methods",
# 	"filters": "workpulse.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "workpulse.install.before_install"
# after_install = "workpulse.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "workpulse.uninstall.before_uninstall"
# after_uninstall = "workpulse.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "workpulse.utils.before_app_install"
# after_app_install = "workpulse.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "workpulse.utils.before_app_uninstall"
# after_app_uninstall = "workpulse.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "workpulse.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "workpulse.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["workpulse.search.awesomebar_results"]

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"workpulse.tasks.all"
# 	],
# 	"daily": [
# 		"workpulse.tasks.daily"
# 	],
# 	"hourly": [
# 		"workpulse.tasks.hourly"
# 	],
# 	"weekly": [
# 		"workpulse.tasks.weekly"
# 	],
# 	"monthly": [
# 		"workpulse.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "workpulse.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "workpulse.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "workpulse.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "workpulse.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["workpulse.utils.before_request"]
# after_request = ["workpulse.utils.after_request"]

# Job Events
# ----------
# before_job = ["workpulse.utils.before_job"]
# after_job = ["workpulse.utils.after_job"]

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
# 	"workpulse.auth.validate"
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
