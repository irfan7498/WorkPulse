import frappe
from frappe.utils import add_days, nowdate


DEMO_PASSWORD = "WorkPulseDemo123!"
COMPANY_NAME = "Demo Company"

DEMO_USERS = (
    {
        "email": "alice@workpulse.test",
        "first_name": "Alice",
        "last_name": "Manager",
        "department": "Operations",
        "roles": ("Employee", "HR Manager"),
    },
    {
        "email": "bob@workpulse.test",
        "first_name": "Bob",
        "last_name": "Engineer",
        "department": "Engineering",
        "roles": ("Employee",),
    },
    {
        "email": "carol@workpulse.test",
        "first_name": "Carol",
        "last_name": "Designer",
        "department": "Design",
        "roles": ("Employee",),
    },
    {
        "email": "david@workpulse.test",
        "first_name": "David",
        "last_name": "Approver",
        "department": "Operations",
        "roles": ("Employee", "Leave Approver"),
    },
)


def seed_demo_data():
    company = _ensure_company()
    departments = {
        name: _ensure_department(name, company)
        for name in ("Engineering", "Design", "Operations")
    }
    employees = {
        user["email"]: _ensure_employee(user, company, departments[user["department"]])
        for user in DEMO_USERS
    }

    _ensure_settings()
    _normalize_analysis_names()
    leave_type = _ensure_leave_type()
    _ensure_holiday_list(company)
    _ensure_leave_allocations(leave_type, employees.values())
    _ensure_tasks(employees["bob@workpulse.test"])
    _ensure_leave_applications(
        company,
        leave_type,
        employees["bob@workpulse.test"],
        employees["carol@workpulse.test"],
        employees["david@workpulse.test"],
    )

    frappe.db.commit()
    _queue_seed_analyses()
    return {
        "company": company,
        "employees": list(employees.values()),
        "leave_type": leave_type,
    }


def _ensure_settings():
    settings = frappe.get_single("WorkPulse Settings")
    defaults = {
        "enabled": 1,
        "daily_hours": 8,
        "meeting_overhead_pct": 10,
        "workload_ceiling_pct": 100,
        "workload_warn_pct": 85,
        "w_skill": 0.4,
        "w_capacity": 0.25,
        "w_history": 0.2,
        "w_reliability": 0.15,
        "default_task_hours": 8,
        "lookahead_days": 7,
        "llm_enabled": 0,
        "ml_enabled": 0,
        "min_samples_for_ml": 300,
    }
    for field, value in defaults.items():
        current = getattr(settings, field, None)
        if current in (None, ""):
            setattr(settings, field, value)
    settings.save(ignore_permissions=True)


def _queue_seed_analyses():
    leaves = frappe.get_all(
        "Leave Application",
        filters={"description": ["like", "WP-Seed:%"], "status": "Open"},
        pluck="name",
    )
    for leave in leaves:
        frappe.enqueue(
            "workpulse.leave_impact.analyzer.run",
            queue="short",
            leave_application=leave,
            job_id=f"leave-impact-{leave}",
            deduplicate=True,
        )


def _normalize_analysis_names():
    candidates = frappe.get_all(
        "Leave Impact Analysis",
        filters={"name": ["in", ["LIA-.#####", "LIA-NEW"]]},
        fields=["name", "leave_application"],
    )
    for candidate in candidates:
        leave_number = candidate.leave_application.rsplit("-", 1)[-1]
        target = f"LIA-{leave_number}"
        if not frappe.db.exists("Leave Impact Analysis", target):
            frappe.rename_doc("Leave Impact Analysis", candidate.name, target, force=True)


def _ensure_company():
    if frappe.db.exists("Company", COMPANY_NAME):
        return COMPANY_NAME

    company = frappe.get_doc(
        {
            "doctype": "Company",
            "company_name": COMPANY_NAME,
            "abbr": "DCO",
            "default_currency": "USD",
            "country": "United States",
        }
    )
    company.insert(ignore_permissions=True)
    return company.name


def _ensure_department(name, company):
    department_name = f"{name} - DCO"
    existing = frappe.db.exists(
        "Department", {"department_name": department_name, "company": company}
    )
    if existing:
        return existing

    department = frappe.get_doc(
        {
            "doctype": "Department",
            "department_name": department_name,
            "company": company,
            "is_group": 0,
        }
    )
    department.insert(ignore_permissions=True)
    return department.name


def _ensure_user(data):
    if frappe.db.exists("User", data["email"]):
        user = frappe.get_doc("User", data["email"])
    else:
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": data["email"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "enabled": 1,
                "send_welcome_email": 0,
                "new_password": DEMO_PASSWORD,
                "roles": [{"role": role} for role in data["roles"]],
            }
        )
        user.insert(ignore_permissions=True)

    for role in data["roles"]:
        if not any(user_role.role == role for user_role in user.roles):
            user.add_roles(role)
    return user


def _ensure_employee(data, company, department):
    user = _ensure_user(data)
    employee_name = f"{data['first_name']} {data['last_name']}"
    employee = frappe.db.exists("Employee", {"user_id": user.name})
    if employee:
        return employee

    employee = frappe.get_doc(
        {
            "doctype": "Employee",
            "employee_name": employee_name,
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "gender": "Prefer not to say",
            "date_of_birth": "1990-01-01",
            "date_of_joining": "2024-01-01",
            "status": "Active",
            "company": company,
            "department": department,
            "user_id": user.name,
        }
    )
    employee.insert(ignore_permissions=True)
    return employee.name


def _ensure_leave_type():
    name = "Annual Leave"
    if frappe.db.exists("Leave Type", name):
        return name

    leave_type = frappe.get_doc(
        {
            "doctype": "Leave Type",
            "leave_type_name": name,
            "max_leaves_allowed": 20,
            "is_optional_leave": 0,
        }
    )
    leave_type.insert(ignore_permissions=True)
    return leave_type.name


def _ensure_holiday_list(company):
    year = nowdate()[:4]
    holiday_list_name = f"{company} Holidays {year}"
    if not frappe.db.exists("Holiday List", holiday_list_name):
        frappe.get_doc(
            {
                "doctype": "Holiday List",
                "holiday_list_name": holiday_list_name,
                "from_date": f"{year}-01-01",
                "to_date": f"{year}-12-31",
            }
        ).insert(ignore_permissions=True)

    filters = {
        "applicable_for": "Company",
        "assigned_to": company,
        "holiday_list": holiday_list_name,
        "from_date": f"{year}-01-01",
    }
    assignment_name = frappe.db.exists("Holiday List Assignment", filters)
    if assignment_name:
        assignment = frappe.get_doc("Holiday List Assignment", assignment_name)
        if assignment.docstatus == 0:
            assignment.submit()
        return holiday_list_name

    assignment = frappe.get_doc(
        {
            "doctype": "Holiday List Assignment",
            **filters,
            "naming_series": "HR-HLA-.YYYY.-",
        }
    )
    assignment.insert(ignore_permissions=True)
    assignment.submit()
    return holiday_list_name


def _ensure_leave_allocations(leave_type, employees):
    year = nowdate()[:4]
    for employee in employees:
        filters = {
            "employee": employee,
            "leave_type": leave_type,
            "from_date": f"{year}-01-01",
            "to_date": f"{year}-12-31",
        }
        allocation_name = frappe.db.exists("Leave Allocation", filters)
        if allocation_name:
            allocation = frappe.get_doc("Leave Allocation", allocation_name)
            if allocation.docstatus == 0:
                allocation.submit()
            continue

        allocation = frappe.get_doc(
            {
                "doctype": "Leave Allocation",
                **filters,
                "new_leaves_allocated": 20,
            }
        )
        allocation.insert(ignore_permissions=True)
        allocation.submit()


def _ensure_tasks(employee):
    start = add_days(nowdate(), 3)
    end = add_days(nowdate(), 5)
    tasks = (
        ("WP-Seed: Client migration", "Urgent"),
        ("WP-Seed: Quarterly report", "High"),
    )
    for subject, priority in tasks:
        if frappe.db.exists("Task", {"subject": subject}):
            continue

        task = frappe.get_doc(
            {
                "doctype": "Task",
                "subject": subject,
                "status": "Open",
                "priority": priority,
                "exp_start_date": start,
                "exp_end_date": end,
            }
        )
        task.insert(ignore_permissions=True)
        if not frappe.db.exists(
            "ToDo",
            {
                "reference_type": "Task",
                "reference_name": task.name,
                "allocated_to": frappe.db.get_value("Employee", employee, "user_id"),
            },
        ):
            frappe.get_doc(
                {
                    "doctype": "ToDo",
                    "status": "Open",
                    "allocated_to": frappe.db.get_value("Employee", employee, "user_id"),
                    "reference_type": "Task",
                    "reference_name": task.name,
                    "description": "Seeded by WorkPulse demo data",
                }
            ).insert(ignore_permissions=True)


def _ensure_leave_applications(company, leave_type, employee, teammate, approver):
    start = add_days(nowdate(), 3)
    end = add_days(nowdate(), 5)
    approver_user = frappe.db.get_value("Employee", approver, "user_id")
    records = (
        (employee, "WP-Seed: primary leave request"),
        (teammate, "WP-Seed: overlapping teammate leave"),
    )
    for employee_name, marker in records:
        if frappe.db.exists("Leave Application", {"description": marker}):
            continue

        application = frappe.get_doc(
            {
                "doctype": "Leave Application",
                "employee": employee_name,
                "leave_type": leave_type,
                "from_date": start,
                "to_date": end,
                "total_leave_days": 3,
                "company": company,
                "leave_approver": approver_user,
                "status": "Open",
                "description": marker,
            }
        )
        application.insert(ignore_permissions=True)
