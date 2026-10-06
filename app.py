from datetime import date, datetime
import io

from flask import Flask, abort, redirect, render_template, request, url_for

import db
from importers import MissingColumnsError, parse_applications_csv, parse_projects_csv, parse_projects_xlsx

app = Flask(__name__)

PROGRAM_NAME = "MasterProjectPlan-SoftwareDevelopment"
AUTHOR_NAME = "Lawrence Brem"
PUBLISHED_DATE = date.today().isoformat()
VERSION = "0.1.0"
ENVIRONMENT = "Local"
DESCRIPTION = "A minimal NCI web application starter"

db.ensure_table_exists(db.PEOPLE_TABLE_NAME)
db.ensure_table_exists(db.APPLICATIONS_TABLE_NAME)
db.ensure_table_exists(db.PROJECTS_TABLE_NAME)
db.seed_if_empty(
    [
        {"first_name": "Jordan", "last_name": "Alvarez", "nih_email": "jordan.alvarez@nih.gov"},
        {"first_name": "Priya", "last_name": "Natarajan", "nih_email": "priya.natarajan@nih.gov"},
    ]
)


@app.template_filter("stage_shorthand")
def stage_shorthand(stage):
    """Abbreviate a project Stage to its word initials, e.g. "Engineering
    Project Execution" -> "EPE", for compact display in the sidebar list."""
    if not stage:
        return ""
    return "".join(word[0].upper() for word in stage.split() if word[0].isalpha())


def _parse_mdy_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%m/%d/%Y").date()
    except ValueError:
        return None


@app.template_filter("timeline_status")
def timeline_status(project):
    """Whether today falls before, within, or after a project's Planned
    Start/End Date range. Returns None if either date is missing/unparseable."""
    start = _parse_mdy_date(project.get("planned_start_date"))
    end = _parse_mdy_date(project.get("planned_end_date"))
    if not start or not end:
        return None
    today = date.today()
    if today < start:
        return "upcoming"
    if today > end:
        return "past-due"
    return "on-track"


@app.context_processor
def inject_layout_metadata():
    return {
        "program_name": PROGRAM_NAME,
        "author_name": AUTHOR_NAME,
        "published_date": PUBLISHED_DATE,
        "version": VERSION,
        "environment": ENVIRONMENT,
    }


@app.route("/")
def index():
    return render_template("home.html", description=DESCRIPTION)


@app.route("/people")
def people_index():
    return render_template(
        "people_list.html", people=db.list_people(), selected=None, mode="empty", active_tab="people"
    )


@app.route("/people/new", methods=["GET", "POST"])
def people_new():
    if request.method == "POST":
        person = db.create_person(
            first_name=request.form["first_name"].strip(),
            last_name=request.form["last_name"].strip(),
            nih_email=request.form["nih_email"].strip(),
        )
        return redirect(url_for("people_view", person_id=person["id"]))
    return render_template(
        "people_list.html", people=db.list_people(), selected=None, mode="add", active_tab="people"
    )


@app.route("/people/<person_id>")
def people_view(person_id):
    person = db.get_person(person_id)
    if person is None:
        abort(404)
    return render_template(
        "people_list.html", people=db.list_people(), selected=person, mode="view", active_tab="people"
    )


@app.route("/people/<person_id>/edit", methods=["GET", "POST"])
def people_edit(person_id):
    person = db.get_person(person_id)
    if person is None:
        abort(404)
    if request.method == "POST":
        person = db.update_person(
            person_id,
            first_name=request.form["first_name"].strip(),
            last_name=request.form["last_name"].strip(),
            nih_email=request.form["nih_email"].strip(),
        )
        return redirect(url_for("people_view", person_id=person_id))
    return render_template(
        "people_list.html", people=db.list_people(), selected=person, mode="edit", active_tab="people"
    )


@app.route("/people/<person_id>/delete", methods=["POST"])
def people_delete(person_id):
    if db.get_person(person_id) is None:
        abort(404)
    db.delete_person(person_id)
    return redirect(url_for("people_index"))


def _distinct_owners(applications):
    owners = {a["it_application_owner"] for a in applications if a.get("it_application_owner")}
    return sorted(owners)


def _application_names_with_projects():
    return {p["configuration_item"] for p in db.list_projects() if p.get("configuration_item")}


@app.route("/applications")
def applications_index():
    applications = db.list_applications()
    return render_template(
        "applications_list.html",
        applications=applications,
        owners=_distinct_owners(applications),
        selected=None,
        application_names_with_projects=_application_names_with_projects(),
        active_tab="applications",
    )


@app.route("/applications/<application_id>")
def applications_view(application_id):
    application = db.get_application(application_id)
    if application is None:
        abort(404)
    applications = db.list_applications()
    linked_projects = [p for p in db.list_projects() if p.get("configuration_item") == application["name"]]
    return render_template(
        "applications_list.html",
        applications=applications,
        owners=_distinct_owners(applications),
        selected=application,
        linked_projects=linked_projects,
        application_names_with_projects=_application_names_with_projects(),
        active_tab="applications",
    )


def _distinct_leads(projects):
    leads = {p["federal_lead"] for p in projects if p.get("federal_lead")}
    return sorted(leads)


@app.route("/projects")
def projects_index():
    projects = db.list_projects()
    application_by_name = {a["name"]: a["id"] for a in db.list_applications()}
    return render_template(
        "projects_list.html",
        projects=projects,
        leads=_distinct_leads(projects),
        selected=None,
        application_by_name=application_by_name,
        active_tab="projects",
    )


@app.route("/projects/<project_id>")
def projects_view(project_id):
    project = db.get_project(project_id)
    if project is None:
        abort(404)
    projects = db.list_projects()
    application_by_name = {a["name"]: a["id"] for a in db.list_applications()}
    return render_template(
        "projects_list.html",
        projects=projects,
        leads=_distinct_leads(projects),
        selected=project,
        application_by_name=application_by_name,
        active_tab="projects",
    )


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/admin")
def admin_index():
    return render_template(
        "admin.html",
        active_tab="admin",
        application_count=len(db.list_applications()),
        project_count=len(db.list_projects()),
        imported_count=request.args.get("imported"),
        imported_type=request.args.get("type"),
        skipped_count=request.args.get("skipped"),
        import_error=request.args.get("error"),
        reset_type=request.args.get("reset"),
    )


@app.route("/admin/import/applications", methods=["POST"])
def admin_import_applications():
    upload = request.files.get("csv_file")
    if not upload or not upload.filename:
        abort(400)
    try:
        result = parse_applications_csv(io.TextIOWrapper(upload.stream, encoding="cp1252"))
    except MissingColumnsError as e:
        return redirect(url_for("admin_index", error=str(e)))
    for fields in result.records:
        db.create_application(**fields)
    return redirect(
        url_for("admin_index", imported=len(result.records), skipped=result.skipped, type="applications")
    )


@app.route("/admin/import/projects", methods=["POST"])
def admin_import_projects():
    upload = request.files.get("projects_file")
    if not upload or not upload.filename:
        abort(400)
    try:
        if upload.filename.lower().endswith(".csv"):
            result = parse_projects_csv(io.TextIOWrapper(upload.stream, encoding="cp1252"))
        else:
            result = parse_projects_xlsx(io.BytesIO(upload.read()))
    except MissingColumnsError as e:
        return redirect(url_for("admin_index", error=str(e)))
    for fields in result.records:
        db.create_project(**fields)
    return redirect(url_for("admin_index", imported=len(result.records), skipped=result.skipped, type="projects"))


@app.route("/admin/reset/applications", methods=["POST"])
def admin_reset_applications():
    db.clear_applications()
    return redirect(url_for("admin_index", reset="applications"))


@app.route("/admin/reset/projects", methods=["POST"])
def admin_reset_projects():
    db.clear_projects()
    return redirect(url_for("admin_index", reset="projects"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
