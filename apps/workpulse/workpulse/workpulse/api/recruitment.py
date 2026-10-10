import json

import frappe

from workpulse.engines.recruitment import sanitize_candidate_profile, score_candidate


@frappe.whitelist()
def score_applicant(job_applicant, team_requirement=None):
    applicant = frappe.get_doc("Job Applicant", job_applicant)
    _require_read(applicant)
    requirement = _get_requirement(team_requirement)
    profile = sanitize_candidate_profile(
        {
            "cover_letter": applicant.cover_letter or "",
            "notes": applicant.notes or "",
            "designation": applicant.designation or "",
            "job_title": applicant.job_title or "",
        }
    )
    text = " ".join(str(value) for value in profile.values()).lower()
    required = requirement.get("requirements", [])
    matched = sum(1 for item in required if item["skill"].lower() in text)
    skill_match = matched / len(required) if required else 0.5
    experience_match = 0.5
    project_similarity = 0.5
    availability = 1.0
    gap_coverage = 1.0
    total = score_candidate(
        skill_match=skill_match,
        experience_match=experience_match,
        project_similarity=project_similarity,
        availability=availability,
        gap_coverage=gap_coverage,
    )
    score_name = frappe.db.exists(
        "WP Candidate Score",
        {"job_applicant": applicant.name, "team_requirement": team_requirement},
    )
    score = frappe.get_doc("WP Candidate Score", score_name) if score_name else frappe.new_doc(
        "WP Candidate Score"
    )
    score.update(
        {
            "job_applicant": applicant.name,
            "team_requirement": team_requirement,
            "sub_scores": json.dumps(
                {
                    "skill_match": skill_match,
                    "experience_match": experience_match,
                    "project_similarity": project_similarity,
                    "availability": availability,
                    "gap_coverage": gap_coverage,
                }
            ),
            "total": total,
            "explanation": "Rule-based score. Protected attributes were excluded.",
            "parsed_resume": json.dumps({"matched_skills": [item["skill"] for item in required if item["skill"].lower() in text]}),
            "status": "Shortlisted" if total >= 0.7 else "Needs Review",
        }
    )
    score.save(ignore_permissions=True)
    return score.as_dict()


@frappe.whitelist()
def list_review_queue(status=None, limit=50):
    if not frappe.has_permission("WP Candidate Score", "read"):
        frappe.throw("You do not have permission to view candidate scores.", frappe.PermissionError)
    filters = {"status": status} if status else {}
    return frappe.get_all(
        "WP Candidate Score",
        filters=filters,
        fields=["name", "job_applicant", "team_requirement", "total", "status", "sub_scores", "explanation"],
        order_by="total desc, modified desc",
        limit_page_length=min(int(limit), 100),
    )


@frappe.whitelist()
def update_review(score_name, status):
    if status not in {"Needs Review", "Shortlisted", "Rejected"}:
        frappe.throw("Invalid candidate review status.")
    score = frappe.get_doc("WP Candidate Score", score_name)
    if not frappe.has_permission("WP Candidate Score", "write", score):
        frappe.throw("You do not have permission to review this candidate.", frappe.PermissionError)
    score.status = status
    score.save()
    return {"name": score.name, "status": score.status}


def _get_requirement(name):
    if not name:
        return {"requirements": []}
    requirement = frappe.get_doc("WP Team Requirement", name)
    if not frappe.has_permission("WP Team Requirement", "read", requirement):
        frappe.throw("You do not have permission to view this requirement.", frappe.PermissionError)
    return {"requirements": [row.as_dict() for row in requirement.requirements]}


def _require_read(applicant):
    if not frappe.has_permission("Job Applicant", "read", applicant):
        frappe.throw("You do not have permission to view this applicant.", frappe.PermissionError)
