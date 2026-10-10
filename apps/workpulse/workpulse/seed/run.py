"""Deterministic, tagged seed data for WorkPulse demos and integration tests."""

from __future__ import annotations

import random
import json
from datetime import date, timedelta
from typing import Any

from .scenarios import ALL_SCENARIO_IDS

SCALE_COUNTS = {
    "small": {"employees": 50, "projects": 10, "tasks": 400},
    "medium": {"employees": 200, "projects": 40, "tasks": 1600},
    "large": {"employees": 2000, "projects": 300, "tasks": 12000},
}
SEED_PREFIX = "WPS-"
PASSWORD = "WorkPulseSeed123!"
FIRST_NAMES = (
    "Aarav", "Aditi", "Amit", "Ananya", "Arjun", "Bhavna", "Dev", "Diya",
    "Isha", "Kabir", "Karan", "Kavya", "Leena", "Maya", "Neha", "Nikhil",
    "Pooja", "Rahul", "Riya", "Rohan", "Sahil", "Samir", "Sneha", "Tanvi",
)
LAST_NAMES = (
    "Sharma", "Verma", "Patel", "Iyer", "Mehta", "Nair", "Rao", "Joshi",
    "Kapoor", "Desai", "Bose", "Menon", "Gupta", "Malhotra", "Kulkarni",
)
DESIGNATIONS = (
    "Backend Developer", "Frontend Developer", "Full-stack Developer",
    "QA Engineer", "DevOps Engineer", "ML Engineer", "Product Manager",
)


def build_seed_manifest(
    seed: int = 42, scale: str = "small", today: date | str | None = None
) -> dict[str, Any]:
    scale_name = str(scale).lower()
    if scale_name not in SCALE_COUNTS:
        raise ValueError(f"Unsupported scale '{scale}'. Allowed: {sorted(SCALE_COUNTS)}")
    today_value = today if isinstance(today, str) else (today or date.today())
    return {
        "seed": int(seed),
        "scale": scale_name,
        "today": str(today_value),
        "counts": dict(SCALE_COUNTS[scale_name]),
        "scenarios": list(ALL_SCENARIO_IDS),
        "tag": "wp_seed",
        "note": "Deterministic synthetic seed for demo and testing",
    }


def main(
    seed: int = 42, scale: str = "small", today: date | str | None = None
) -> dict[str, Any]:
    """Create tagged seed data when invoked through bench, otherwise return the contract."""
    manifest = build_seed_manifest(seed=seed, scale=scale, today=today)
    try:
        import frappe
    except ImportError:
        return manifest

    if not getattr(frappe.local, "site", None):
        return manifest

    today_value = _as_date(today)
    frappe.flags.in_import = True
    frappe.flags.mute_emails = True
    try:
        result = _seed_frappe(frappe, seed, scale.lower(), today_value)
        frappe.db.commit()
        return {**manifest, "created": result}
    finally:
        frappe.flags.in_import = False
        frappe.flags.mute_emails = False


def wipe() -> dict[str, Any]:
    """Delete only records created by this generator, in dependency order."""
    try:
        import frappe
    except ImportError:
        return {"tag": "wp_seed", "deleted": {}}
    if not getattr(frappe.local, "site", None):
        return {"tag": "wp_seed", "deleted": {}}

    deleted = {}
    for doctype in (
        "WP Candidate Score", "Job Applicant", "Leave Application", "ToDo", "WP Team", "Task", "Project", "WP Portfolio",
        "Employee", "User",
    ):
        names = _seed_names(frappe, doctype)
        for name in names:
            if doctype == "User" and name == frappe.session.user:
                continue
            frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
        deleted[doctype] = len(names)
    frappe.db.commit()
    return {"tag": "wp_seed", "deleted": deleted}


def _seed_frappe(frappe, seed: int, scale: str, today: date) -> dict[str, int]:
    rng = random.Random(seed)
    counts = SCALE_COUNTS[scale]
    company = _ensure_company(frappe)
    departments = [_ensure_department(frappe, name, company) for name in (
        "Engineering", "QA", "DevOps", "Data/ML", "Product", "HR",
    )]
    designations = [_ensure_designation(frappe, name) for name in DESIGNATIONS]
    holiday_list = _ensure_seed_holiday_list(frappe, company, today)
    employees = _create_employees(
        frappe, rng, counts["employees"], company, departments, designations, today
    )
    for employee in employees:
        frappe.db.set_value("Employee", employee, "holiday_list", holiday_list, update_modified=False)
        _ensure_seed_holiday_assignment(frappe, employee, holiday_list, company, today)
    portfolios = _create_portfolios(frappe, counts["projects"])
    _ensure_project_portfolio_field(frappe)
    projects = _create_projects(frappe, counts["projects"], portfolios, today)
    _create_teams(frappe, employees, projects, today)
    tasks = _create_tasks(frappe, rng, counts["tasks"], employees, projects, today)
    timesheets = _create_timesheets(frappe, rng, employees, projects, today)
    candidates = _create_candidates(frappe, counts["employees"], today)
    model_versions = _create_model_versions(frappe, today)
    leave_applications = _create_leave_scenarios(frappe, employees, company, today)
    return {
        "employees": len(employees),
        "portfolios": len(portfolios),
        "projects": len(projects),
        "tasks": tasks,
        "timesheets": timesheets,
        "candidates": candidates,
        "model_versions": model_versions,
        "leave_applications": leave_applications,
    }


def _create_employees(frappe, rng, count, company, departments, designations, today):
    employees = []
    for index in range(count):
        first = FIRST_NAMES[index % len(FIRST_NAMES)]
        last = LAST_NAMES[(index // len(FIRST_NAMES)) % len(LAST_NAMES)]
        email = f"wps{index + 1:03d}@workpulse.test"
        if not frappe.db.exists("User", email):
            user = frappe.get_doc({
                "doctype": "User", "email": email, "first_name": first,
                "last_name": f"{last}{index + 1}", "enabled": 1,
                "send_welcome_email": 0, "new_password": PASSWORD,
                "roles": [{"role": "Employee"}],
            })
            user.insert(ignore_permissions=True)
        employee_name = f"{SEED_PREFIX}EMP-{index + 1:03d}"
        employee = frappe.db.exists("Employee", {"user_id": email})
        if not employee:
            employee = frappe.db.exists("Employee", {"employee_name": employee_name})
        if not employee:
            employee = frappe.get_doc({
                "doctype": "Employee", "employee_name": employee_name,
                "first_name": first, "last_name": f"{last}{index + 1}",
                "gender": "Prefer not to say",
                "date_of_birth": date(1985, 1, 1) + timedelta(days=index % 5000),
                "date_of_joining": today - timedelta(days=rng.randint(365, 8 * 365)),
                "status": "Active", "company": company,
                "department": departments[index % len(departments)],
                "designation": designations[index % len(designations)],
                "user_id": email,
            })
            employee.insert(ignore_permissions=True)
            employee = employee.name
        employees.append(employee)
    return employees


def _create_portfolios(frappe, count):
    portfolios = []
    for index in range(3):
        name = f"{SEED_PREFIX}Portfolio-{index + 1}"
        if not frappe.db.exists("WP Portfolio", name):
            frappe.get_doc({
                "doctype": "WP Portfolio", "portfolio_name": name, "is_group": 1,
            }).insert(ignore_permissions=True)
        portfolios.append(name)
    return portfolios


def _create_projects(frappe, count, portfolios, today):
    projects = []
    for index in range(count):
        project_name = f"{SEED_PREFIX}Project-{index + 1:02d}"
        existing = frappe.db.exists("Project", {"project_name": project_name})
        if existing:
            frappe.db.set_value(
                "Project", existing, "wp_portfolio", portfolios[index % len(portfolios)],
                update_modified=False,
            )
            projects.append(existing)
            continue
        project = frappe.get_doc({
            "doctype": "Project", "project_name": project_name,
            "wp_portfolio": portfolios[index % len(portfolios)],
            "status": ("Completed" if index < 4 else "Open" if index < 8 else "Planned"),
            "expected_start_date": today - timedelta(days=90),
            "expected_end_date": today + timedelta(days=90),
        })
        project.insert(ignore_permissions=True)
        projects.append(project.name)
    return projects


def _ensure_project_portfolio_field(frappe):
    if frappe.get_meta("Project").has_field("wp_portfolio"):
        return
    frappe.get_doc({
        "doctype": "Custom Field", "dt": "Project", "fieldname": "wp_portfolio",
        "label": "WorkPulse Portfolio", "fieldtype": "Link",
        "options": "WP Portfolio", "insert_after": "project_name",
    }).insert(ignore_permissions=True)


def _create_teams(frappe, employees, projects, today):
    for index, project in enumerate(projects):
        team_name = f"{SEED_PREFIX}Team-{index + 1:02d}"
        if frappe.db.exists("WP Team", team_name):
            continue
        team = frappe.get_doc({
            "doctype": "WP Team", "team_name": team_name, "project": project,
            "lead": employees[index % len(employees)],
        })
        for offset in range(5):
            team.append("members", {
                "employee": employees[(index * 5 + offset) % len(employees)],
                "role": DESIGNATIONS[(index + offset) % len(DESIGNATIONS)],
                "allocation_pct": 60 if offset == 0 else 20,
                "from_date": today - timedelta(days=30),
                "to_date": today + timedelta(days=90),
            })
        team.insert(ignore_permissions=True)


def _create_tasks(frappe, rng, count, employees, projects, today):
    created = 0
    for index in range(count):
        subject = f"{SEED_PREFIX}Task-{index + 1:04d}"
        if frappe.db.exists("Task", {"subject": subject}):
            continue
        project = projects[index % len(projects)]
        status = "Completed" if index % 5 == 0 else "Open"
        task = frappe.get_doc({
            "doctype": "Task", "subject": subject, "project": project,
            "status": status, "priority": ("High" if index % 11 == 0 else "Medium"),
            "expected_time": rng.randint(4, 40),
            "exp_start_date": today - timedelta(days=rng.randint(0, 30)),
            "exp_end_date": today + timedelta(days=rng.randint(1, 60)),
        })
        task.insert(ignore_permissions=True)
        if index % 13 != 0:
            employee = employees[index % len(employees)]
            user = frappe.db.get_value("Employee", employee, "user_id")
            if user:
                frappe.get_doc({
                    "doctype": "ToDo", "status": "Closed" if status == "Completed" else "Open",
                    "allocated_to": user, "reference_type": "Task",
                    "reference_name": task.name, "description": "WorkPulse seeded assignment",
                }).insert(ignore_permissions=True)
        created += 1
    for index in (1, 2):
        subject = f"{SEED_PREFIX}S5-High-Priority-{index}"
        if frappe.db.exists("Task", {"subject": subject}):
            continue
        task = frappe.get_doc({
            "doctype": "Task",
            "subject": subject,
            "project": projects[0],
            "status": "Open",
            "priority": "High",
            "expected_time": 16,
            "exp_start_date": today,
            "exp_end_date": today + timedelta(days=3),
        })
        task.insert(ignore_permissions=True)
        user = frappe.db.get_value("Employee", employees[0], "user_id")
        frappe.get_doc({
            "doctype": "ToDo",
            "status": "Open",
            "allocated_to": user,
            "reference_type": "Task",
            "reference_name": task.name,
            "description": "WorkPulse seeded S5 leave-impact assignment",
        }).insert(ignore_permissions=True)
        created += 1
    return created


def _create_timesheets(frappe, rng, employees, projects, today):
    created = 0
    for index, employee in enumerate(employees):
        name = f"{SEED_PREFIX}Timesheet-{index + 1:03d}"
        if frappe.db.exists("Timesheet", {"title": name}):
            continue
        timesheet = frappe.get_doc({
            "doctype": "Timesheet",
            "title": name,
            "employee": employee,
            "company": frappe.db.get_value("Employee", employee, "company"),
            "start_date": today - timedelta(days=14),
            "end_date": today,
        })
        timesheet.append("time_logs", {
            "activity_type": "Execution",
            "from_time": f"{today - timedelta(days=7)} 09:00:00",
            "to_time": f"{today - timedelta(days=7)} {9 + rng.randint(4, 8):02d}:00:00",
            "hours": rng.randint(4, 8),
            "project": projects[index % len(projects)],
        })
        timesheet.insert(ignore_permissions=True)
        timesheet.submit()
        created += 1
    return created


def _create_candidates(frappe, employee_count, today):
    profiles = [
        ("Asha Candidate", "asha.candidate", "Python, SQL, Frappe, project delivery"),
        ("Bilal Candidate", "bilal.candidate", "Python, JavaScript, React, API design"),
        ("Chen Candidate", "chen.candidate", "SQL, analytics, dashboards, data modeling"),
        ("Divya Candidate", "divya.candidate", "DevOps, Docker, Kubernetes, Linux"),
        ("Evan Candidate", "evan.candidate", "JavaScript, CSS, documentation"),
        ("Fatima Candidate", "fatima.candidate", "Python, testing, QA automation"),
    ]
    created = 0
    for index, (name, email_prefix, skills) in enumerate(profiles):
        email = f"{email_prefix}@workpulse.test"
        if frappe.db.exists("Job Applicant", {"email_id": email}):
            continue
        applicant = frappe.get_doc({
            "doctype": "Job Applicant",
            "applicant_name": name,
            "email_id": email,
            "status": "Open",
            "cover_letter": (
                f"{SEED_PREFIX} Candidate {index + 1}. "
                f"Demonstrated experience with {skills}. "
                f"Available for delivery work starting {today}."
            ),
        })
        applicant.insert(ignore_permissions=True)
        created += 1
    return created


def _create_model_versions(frappe, today):
    models = [
        ("delay_probability", "rules-baseline-1", {"brier_score": 0.24, "source": "rules"}),
        ("workload_estimation", "rules-baseline-1", {"mae": 0.0, "source": "rules"}),
    ]
    created = 0
    for model_name, version, metrics in models:
        if frappe.db.exists("WP Model Version", {"model_name": model_name, "version": version}):
            continue
        doc = frappe.get_doc({
            "doctype": "WP Model Version",
            "model_name": model_name,
            "version": version,
            "status": "Candidate",
            "metrics": json.dumps(metrics),
            "training_end_date": today,
            "notes": "Seeded rule-based baseline; requires evaluation before activation.",
        })
        doc.insert(ignore_permissions=True)
        created += 1
    return created


def _create_leave_scenarios(frappe, employees, company, today):
    leave_type = _ensure_seed_leave_type(frappe)
    _ensure_seed_leave_allocations(frappe, employees, leave_type, today)
    primary = employees[0]
    teammates = [employees[index] for index in (6, 12)]
    approver = frappe.db.get_value("Employee", employees[-1], "user_id")
    records = [
        (primary, today + timedelta(days=2), today + timedelta(days=4), "S5 high-risk leave"),
        (teammates[0], today + timedelta(days=2), today + timedelta(days=4), "S6 overlap leave A"),
        (teammates[1], today + timedelta(days=2), today + timedelta(days=4), "S6 overlap leave B"),
    ]
    created = 0
    for employee, start, end, scenario in records:
        marker = f"{SEED_PREFIX}{scenario}"
        if frappe.db.exists("Leave Application", {"description": marker}):
            continue
        leave = frappe.get_doc({
            "doctype": "Leave Application",
            "employee": employee,
            "employee_name": frappe.db.get_value("Employee", employee, "employee_name"),
            "leave_type": leave_type,
            "from_date": start,
            "to_date": end,
            "total_leave_days": (end - start).days + 1,
            "company": company,
            "posting_date": today,
            "leave_approver": approver,
            "status": "Open",
            "description": marker,
        })
        leave.insert(ignore_permissions=True)
        created += 1
    return created


def _ensure_seed_leave_type(frappe):
    if frappe.db.exists("Leave Type", "WorkPulse Seed Leave"):
        return "WorkPulse Seed Leave"
    leave_type = frappe.get_doc({
        "doctype": "Leave Type",
        "leave_type_name": "WorkPulse Seed Leave",
        "max_leaves_allowed": 30,
        "is_optional_leave": 0,
    })
    leave_type.insert(ignore_permissions=True)
    return leave_type.name


def _ensure_seed_holiday_list(frappe, company, today):
    name = f"{SEED_PREFIX}Holiday List {today.year}"
    if not frappe.db.exists("Holiday List", name):
        holiday_list = frappe.get_doc({
            "doctype": "Holiday List",
            "holiday_list_name": name,
            "from_date": f"{today.year}-01-01",
            "to_date": f"{today.year}-12-31",
        })
        holiday_list.insert(ignore_permissions=True)
    return name


def _ensure_seed_holiday_assignment(frappe, employee, holiday_list, company, today):
    filters = {
        "assigned_to": employee,
        "holiday_list": holiday_list,
        "from_date": f"{today.year}-01-01",
    }
    existing = frappe.db.get_value("Holiday List Assignment", filters, "name")
    if existing:
        assignment = frappe.get_doc("Holiday List Assignment", existing)
        if assignment.docstatus == 0:
            assignment.submit()
        return
    assignment = frappe.get_doc({
        "doctype": "Holiday List Assignment",
        **filters,
        "employee_company": company,
        "applicable_for": "Employee",
    })
    assignment.insert(ignore_permissions=True)
    assignment.submit()


def _ensure_seed_leave_allocations(frappe, employees, leave_type, today):
    for employee in employees:
        filters = {
            "employee": employee,
            "leave_type": leave_type,
            "from_date": f"{today.year}-01-01",
            "to_date": f"{today.year}-12-31",
        }
        if frappe.db.exists("Leave Allocation", filters):
            continue
        allocation = frappe.get_doc({
            "doctype": "Leave Allocation",
            **filters,
            "new_leaves_allocated": 30,
        })
        allocation.insert(ignore_permissions=True)
        allocation.submit()


def _ensure_company(frappe):
    if frappe.db.exists("Company", "WorkPulse Seed Company"):
        return "WorkPulse Seed Company"
    company = frappe.get_doc({
        "doctype": "Company", "company_name": "WorkPulse Seed Company",
        "abbr": "WPS", "default_currency": "USD", "country": "United States",
        "valuation_method": "Moving Average",
    })
    company.insert(ignore_permissions=True)
    return company.name


def _ensure_department(frappe, name, company):
    department_name = f"{name} - WPS"
    existing = frappe.db.exists("Department", {
        "department_name": department_name, "company": company,
    })
    if existing:
        return existing
    department = frappe.get_doc({
        "doctype": "Department", "department_name": department_name,
        "company": company, "is_group": 0,
    })
    department.insert(ignore_permissions=True)
    return department.name


def _ensure_designation(frappe, name):
    if frappe.db.exists("Designation", name):
        return name
    designation = frappe.get_doc({"doctype": "Designation", "designation_name": name})
    designation.insert(ignore_permissions=True)
    return designation.name


def _seed_names(frappe, doctype):
    if doctype == "User":
        return frappe.get_all(doctype, filters={"name": ["like", "wps%"]}, pluck="name")
    if doctype == "Employee":
        return frappe.get_all(doctype, filters={"user_id": ["like", "wps%"]}, pluck="name")
    field = {"Task": "subject", "Project": "project_name", "WP Team": "team_name",
             "WP Portfolio": "portfolio_name", "Employee": "employee_name"}.get(doctype)
    if not field:
        return []
    return frappe.get_all(doctype, filters={field: ["like", f"{SEED_PREFIX}%"]}, pluck="name")


def _as_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(value) if value else date.today()
