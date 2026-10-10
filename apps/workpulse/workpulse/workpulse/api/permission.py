import frappe


def has_app_permission():
    return bool(frappe.session.user and frappe.session.user != "Guest")
