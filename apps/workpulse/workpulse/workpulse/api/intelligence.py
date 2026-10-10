import json

import frappe
from frappe.utils import now_datetime

from workpulse.llm.assistant import build_assistant_response
from workpulse.llm.client import complete_chat, detect_prompt_injection, get_provider_status


@frappe.whitelist()
def list_model_versions(limit=50):
    _require_role({"System Manager", "HR Manager", "Projects Manager"})
    models = frappe.get_all(
        "WP Model Version",
        fields=["name", "model_name", "version", "status", "metrics", "activated_on"],
        order_by="modified desc",
        limit_page_length=min(int(limit), 100),
    )
    for model in models:
        model["evaluation_passed"] = bool(
            frappe.db.exists(
                "WP Model Evaluation",
                {"model_version": model.name, "passed": 1},
            )
        )
    return models


@frappe.whitelist()
def activate_model(name):
    _require_role({"System Manager"})
    model = frappe.get_doc("WP Model Version", name)
    if model.status not in {"Candidate", "Active"}:
        frappe.throw("Only candidate or active models can be activated.")
    settings = frappe.get_single("WorkPulse Settings")
    if not settings.ml_enabled:
        frappe.throw("ML is disabled in WorkPulse Settings.")
    if not frappe.db.exists(
        "WP Model Evaluation", {"model_version": model.name, "passed": 1}
    ):
        frappe.throw("Model must pass evaluation against the baseline before activation.")
    for existing in frappe.get_all(
        "WP Model Version", filters={"model_name": model.model_name, "status": "Active"}, pluck="name"
    ):
        frappe.db.set_value("WP Model Version", existing, "status", "Retired")
    model.update({"status": "Active", "activated_by": frappe.session.user, "activated_on": now_datetime()})
    model.save(ignore_permissions=True)
    return {"name": model.name, "status": model.status}


@frappe.whitelist()
def evaluate_model(name, baseline_metric, candidate_metric, metric_name="metric"):
    _require_role({"System Manager"})
    model = frappe.get_doc("WP Model Version", name)
    baseline = float(baseline_metric)
    candidate = float(candidate_metric)
    passed = candidate < baseline
    evaluation = frappe.get_doc({
        "doctype": "WP Model Evaluation",
        "model_version": model.name,
        "baseline_metric": baseline,
        "candidate_metric": candidate,
        "metric_name": metric_name,
        "passed": passed,
        "evaluated_by": frappe.session.user,
        "evaluated_on": now_datetime(),
        "notes": "Candidate must improve the lower-is-better baseline metric.",
    })
    evaluation.insert(ignore_permissions=True)
    return {"name": evaluation.name, "passed": passed}


@frappe.whitelist()
def ask(question):
    _require_role({"System Manager", "HR Manager", "Projects Manager"})
    if not isinstance(question, str) or not question.strip():
        frappe.throw("A question is required.")
    if detect_prompt_injection(question):
        frappe.throw("The assistant rejected this request as an unsafe instruction.")
    settings = frappe.get_single("WorkPulse Settings")
    provider = get_provider_status(settings)
    if not settings.llm_enabled:
        return {"enabled": False, "configured": provider["configured"], "answer": "The assistant is disabled. Enable it in WorkPulse Settings to continue."}
    tools = []
    if frappe.has_permission("WP Project Snapshot", "read"):
        tools.append("project snapshots")
    if frappe.has_permission("WP Workload Snapshot", "read"):
        tools.append("workload snapshots")
    context = []
    if "project snapshots" in tools:
        high = frappe.db.count("WP Project Snapshot", {"risk_level": "High"})
        context.append(f"{high} high-risk project snapshots are currently visible")
    if "workload snapshots" in tools:
        overloaded = frappe.db.count("WP Workload Snapshot", {"workload_pct": [">", 100]})
        context.append(f"{overloaded} workload snapshots exceed capacity")
    if provider["configured"]:
        answer = complete_chat(
            settings,
            [
                {"role": "system", "content": "Answer only from the provided visible facts. Do not invent data or perform actions."},
                {"role": "user", "content": f"Question: {question}\nVisible facts: {context}"},
            ],
        )
        source = "provider"
    else:
        answer = build_assistant_response(question, tools=tools, context=context)
        source = "deterministic-fallback"
    return {"enabled": True, "configured": provider["configured"], "source": source, "answer": answer, "tools": tools, "context": context}


@frappe.whitelist()
def provider_status():
    _require_role({"System Manager", "HR Manager", "Projects Manager"})
    settings = frappe.get_single("WorkPulse Settings")
    status = get_provider_status(settings)
    status.pop("key_env", None)
    return status


def _require_role(roles):
    if not roles.intersection(frappe.get_roles()):
        frappe.throw("You do not have permission to use WorkPulse intelligence.", frappe.PermissionError)
