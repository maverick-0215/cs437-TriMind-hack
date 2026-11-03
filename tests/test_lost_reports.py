from datetime import date

from app.models import LostReport
from conftest import REPORT_DEFAULTS


def test_S11_student_can_file_lost_report(student, add_report):
    report = add_report(student)
    assert report.category == "Bottle"
    assert report.title == "My blue bottle"
    assert report.date_lost == date(2026, 10, 2)
    assert report.place_lost == "Library"
    assert report.private_details == REPORT_DEFAULTS["private_details"]
    assert report.student.email == "asha@iitgn.ac.in"
    assert "My blue bottle" in student.get("/reports").get_data(as_text=True)


def test_S11_logged_out_user_cannot_file_report(anon):
    resp = anon.post("/reports/new", data=REPORT_DEFAULTS)
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]
    assert LostReport.query.count() == 0


def test_S11_missing_field_is_rejected(student):
    resp = student.post("/reports/new", data={**REPORT_DEFAULTS, "place_lost": ""})
    assert resp.status_code == 400
    assert LostReport.query.count() == 0


def test_S12_student_sees_only_own_reports(student, other, add_report):
    mine = add_report(student, title="Asha's bottle", private_details="ASHA-SECRET")
    theirs = add_report(other, title="Ravi's bottle", private_details="RAVI-SECRET")

    page = student.get("/reports").get_data(as_text=True)
    assert "Asha&#39;s bottle" in page
    assert "Ravi" not in page

    assert student.get(f"/reports/{mine.id}").status_code == 200
    resp = student.get(f"/reports/{theirs.id}")
    assert resp.status_code in (403, 404)
    assert "RAVI-SECRET" not in resp.get_data(as_text=True)
