from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect("application.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    cursor.execute("PRAGMA table_info(applications)")
    columns = [column[1] for column in cursor.fetchall()]

    if "job_url" not in columns:
        cursor.execute("ALTER TABLE applications ADD COLUMN job_url TEXT")

    if "application_date" not in columns:
        cursor.execute("ALTER TABLE applications ADD COLUMN application_date TEXT")

    if "notes" not in columns:
        cursor.execute("ALTER TABLE applications ADD COLUMN notes TEXT")

    conn.commit()
    conn.close()


@app.route("/")
def home():
    search = request.args.get("search", "")
    status_filter = request.args.get("status", "")
    sort_order = request.args.get("sort", "newest")

    conn = sqlite3.connect("application.db")
    cursor = conn.cursor()

    # Dashboard counts
    cursor.execute("SELECT COUNT(*) FROM applications")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Applied'")
    applied = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Interview'")
    interviews = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Offer'")
    offers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Rejected'")
    rejected = cursor.fetchone()[0]

    if total > 0:
        interview_rate = round((interviews / total) * 100, 1)
    else:
        interview_rate = 0

    if total > 0:
        offer_rate = round((offers / total) * 100, 1)
    else:
        offer_rate = 0

    # Get all applications
    query = """
        SELECT id, company, role, job_url, application_date, status, notes
        FROM applications
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND (company LIKE ? OR role LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    if sort_order == "oldest":
        query += " ORDER BY application_date ASC"
    else:
        query += " ORDER BY application_date DESC"

    cursor.execute(query, params)

    applications = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        total=total,
        applied=applied,
        interviews=interviews,
        offers=offers,
        rejected=rejected,
        interview_rate=interview_rate,
        offer_rate=offer_rate,
        applications=applications,
        search=search,
        status_filter=status_filter,
        sort_order=sort_order
    )

@app.route("/add")
def add_application():
    return render_template("add_application.html")

@app.route("/submit", methods=["POST"])
def submit():
    company = request.form["company"]
    role = request.form["role"]
    job_url = request.form["job_url"]
    application_date = request.form["application_date"]
    status = request.form["status"]
    notes = request.form["notes"]

    conn = sqlite3.connect("application.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO applications (company, role, job_url, application_date, status, notes) VALUES (?, ?, ?, ?, ?, ?)""",
        (company, role, job_url, application_date, status, notes)
    )

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/edit/<int:application_id>", methods=["GET", "POST"])
def edit_application(application_id):

    conn = sqlite3.connect("application.db")
    cursor = conn.cursor()

    if request.method == "POST":
        company = request.form["company"]
        role = request.form["role"]
        job_url = request.form["job_url"]
        application_date = request.form["application_date"]
        status = request.form["status"]
        notes = request.form["notes"]

        cursor.execute("""
            UPDATE applications
            SET company = ?,
                role = ?,
                job_url = ?,
                application_date = ?,
                status = ?,
                notes = ?
            WHERE id = ?
        """, (
            company,
            role,
            job_url,
            application_date,
            status,
            notes,
            application_id
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    cursor.execute("""
        SELECT id, company, role, job_url, application_date, status, notes
        FROM applications
        WHERE id = ?
    """, (application_id,))

    application = cursor.fetchone()

    conn.close()

    return render_template("edit.html", application=application)

@app.route("/application/<int:application_id>")
def application_details(application_id):

    conn = sqlite3.connect("application.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, company, role, job_url, application_date, status, notes
        FROM applications
        WHERE id = ?
    """, (application_id,))

    application = cursor.fetchone()

    conn.close()

    if application is None:
        return "Application not found", 404

    return render_template(
        "application_details.html",
        application=application
    )

@app.route("/delete/<int:application_id>", methods=["POST"])
def delete_application(application_id):
    conn = sqlite3.connect("application.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM applications WHERE id = ?",
        (application_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)