import os
import re
import secrets
import uuid
from datetime import date, datetime
from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from . import db, login_manager
from .models import CATEGORIES, Claim, FoundItem, Handover, LostReport, Notification, User

bp = Blueprint("main", __name__)

IITGN_EMAIL = re.compile(r"^[^@\s]+@iitgn\.ac\.in$")
PHOTO_TYPES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


# ---------- helpers ----------

def admin_required(view):
    """S3: logged-out users go to login; logged-in non-admins get 403."""

    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def read_form(fields, date_field=None):
    """Read required text fields. Returns (data, errors)."""
    data = {f: request.form.get(f, "").strip() for f in fields}
    errors = [f"{f.replace('_', ' ').capitalize()} is required." for f in fields if not data[f]]
    if data.get("category") and data["category"] not in CATEGORIES:
        errors.append("Choose a category from the list.")
    if date_field and data[date_field]:
        data[date_field] = parse_date(data[date_field])
        if data[date_field] is None:
            errors.append("Enter a valid date.")
    return data, errors


def show_errors(errors):
    for e in errors:
        flash(e, "error")


def notify(user_id, message):
    db.session.add(Notification(user_id=user_id, message=message))


def suggest_reports(item):
    """S13: unlinked reports, same category, lost on or before the found date."""
    return (
        LostReport.query.filter(
            LostReport.linked_item_id.is_(None),
            LostReport.category == item.category,
            LostReport.date_lost <= item.date_found,
        )
        .order_by(LostReport.date_lost.desc())
        .all()
    )


def available_items(args):
    """S6, S8–S10, S22: only AVAILABLE items, filtered, newest first."""
    query = FoundItem.query.filter_by(status="AVAILABLE")
    if args.get("category"):
        query = query.filter(FoundItem.category == args["category"])
    if start := parse_date(args.get("from")):
        query = query.filter(FoundItem.date_found >= start)
    if end := parse_date(args.get("to")):
        query = query.filter(FoundItem.date_found <= end)
    if keyword := args.get("q", "").strip():
        query = query.filter(
            db.or_(
                FoundItem.title.icontains(keyword, autoescape=True),
                FoundItem.category.icontains(keyword, autoescape=True),
            )
        )
    return query.order_by(FoundItem.date_found.desc(), FoundItem.id.desc()).all()


@bp.app_context_processor
def template_globals():
    unread = 0
    if current_user.is_authenticated:
        unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return {"unread_count": unread, "categories": CATEGORIES, "today": date.today()}


# ---------- login required everywhere (S23) ----------

OPEN_ENDPOINTS = {"main.login", "main.signup", "static"}


@bp.before_app_request
def require_login():
    """S23: logged-out visitors may only open the login and sign-up pages."""
    if current_user.is_authenticated or request.endpoint in OPEN_ENDPOINTS:
        return None
    if request.endpoint is None:  # unknown URL: let it 404
        return None
    if request.path.startswith("/api/"):
        return jsonify(error="Log in to see found items."), 401
    return login_manager.unauthorized()  # redirect to /login?next=...


# ---------- found-items list ----------

@bp.route("/")
def index():
    return render_template("index.html", items=available_items(request.args), args=request.args)


@bp.route("/api/items")
def api_items():
    return jsonify([item.public_dict() for item in available_items(request.args)])


# ---------- auth ----------

@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        data, errors = read_form(("name", "email", "password"))
        email = data["email"].lower()
        if email and not IITGN_EMAIL.match(email):
            errors.append("Only @iitgn.ac.in emails can sign up.")
        elif email and User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
        if not errors:
            user = User(name=data["name"], email=email)
            user.set_password(data["password"])
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("main.index"))
        show_errors(errors)
        return render_template("auth.html", mode="signup"), 400
    return render_template("auth.html", mode="signup")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not IITGN_EMAIL.match(email):
            show_errors(["Only @iitgn.ac.in emails can log in."])
            return render_template("auth.html", mode="login"), 400
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            show_errors(["Wrong email or password."])
            return render_template("auth.html", mode="login"), 400
        login_user(user)
        return redirect(url_for("main.admin_dashboard" if user.is_admin else "main.index"))
    return render_template("auth.html", mode="login")


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("main.login"))


# ---------- student: lost reports ----------

REPORT_FIELDS = ("category", "title", "date_lost", "place_lost", "private_details")


@bp.route("/reports")
@login_required
def reports():
    mine = (
        LostReport.query.filter_by(student_id=current_user.id)
        .order_by(LostReport.created_at.desc())
        .all()
    )
    return render_template("reports.html", reports=mine)


@bp.route("/reports/new", methods=["GET", "POST"])
@login_required
def report_new():
    if request.method == "POST":
        data, errors = read_form(REPORT_FIELDS, date_field="date_lost")
        if not errors:
            report = LostReport(student_id=current_user.id, **data)
            db.session.add(report)
            db.session.commit()
            flash("Lost report filed. We will notify you if a matching item comes in.")
            return redirect(url_for("main.report_detail", report_id=report.id))
        show_errors(errors)
        return render_template("report_new.html", form=request.form), 400
    return render_template("report_new.html", form={})


@bp.route("/reports/<int:report_id>")
@login_required
def report_detail(report_id):
    report = db.session.get(LostReport, report_id)
    if report is None or report.student_id != current_user.id:  # S12
        abort(404)
    return render_template("report_detail.html", report=report)


# ---------- student: claims and notifications ----------

@bp.route("/items/<int:item_id>/claim", methods=["GET", "POST"])
@login_required
def claim_item(item_id):
    item = db.get_or_404(FoundItem, item_id)
    if item.status != "AVAILABLE":
        flash("This item is not available to claim.", "error")
        return redirect(url_for("main.index"))
    if request.method == "POST":
        features = request.form.get("features", "").strip()
        if not features:
            show_errors(["Describe the item's identifying features."])
            return render_template("claim.html", item=item), 400
        # Only move AVAILABLE -> CLAIMED, so two claims at once cannot both win (S16).
        updated = FoundItem.query.filter_by(id=item.id, status="AVAILABLE").update(
            {"status": "CLAIMED"}
        )
        if not updated:
            db.session.rollback()
            flash("This item is not available to claim.", "error")
            return redirect(url_for("main.index"))
        db.session.add(Claim(item_id=item.id, student_id=current_user.id, features=features))
        db.session.commit()
        flash("Claim submitted. Security will review it.")
        return redirect(url_for("main.claims"))
    return render_template("claim.html", item=item)


@bp.route("/claims")
@login_required
def claims():
    mine = Claim.query.filter_by(student_id=current_user.id).order_by(Claim.created_at.desc()).all()
    return render_template("claims.html", claims=mine)


@bp.route("/notifications")
@login_required
def notifications():
    mine = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .all()
    )
    unread_ids = {n.id for n in mine if not n.is_read}
    for n in mine:
        n.is_read = True
    db.session.commit()
    return render_template("notifications.html", notifications=mine, unread_ids=unread_ids)


# ---------- admin ----------

ITEM_FIELDS = ("category", "title", "date_found", "general_area", "exact_location", "description")


@bp.route("/admin")
@admin_required
def admin_dashboard():
    items = FoundItem.query.order_by(FoundItem.created_at.desc()).all()
    pending = Claim.query.filter_by(status="PENDING").order_by(Claim.created_at).all()
    handovers = Handover.query.order_by(Handover.handed_over_at.desc()).all()
    return render_template("admin_dashboard.html", items=items, pending=pending, handovers=handovers)


@bp.route("/admin/items/new", methods=["GET", "POST"])
@admin_required
def admin_item_new():
    if request.method == "POST":
        data, errors = read_form(ITEM_FIELDS, date_field="date_found")
        photo = request.files.get("photo")
        ext = ""
        if photo and photo.filename:
            ext = os.path.splitext(photo.filename)[1].lower()
            if ext not in PHOTO_TYPES:
                errors.append("Photo must be a JPG, PNG, GIF or WEBP image.")
        if not errors:
            item = FoundItem(**data)
            if ext:
                filename = uuid.uuid4().hex + ext
                photo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                item.photo_path = filename
            db.session.add(item)
            db.session.commit()
            flash("Item added.")
            return redirect(url_for("main.admin_item", item_id=item.id))
        show_errors(errors)
        return render_template("admin_item_new.html", form=request.form), 400
    return render_template("admin_item_new.html", form={})


@bp.route("/admin/items/<int:item_id>")
@admin_required
def admin_item(item_id):
    item = db.get_or_404(FoundItem, item_id)
    return render_template(
        "admin_item.html",
        item=item,
        suggestions=suggest_reports(item),
        unlinked=LostReport.query.filter(LostReport.linked_item_id.is_(None)).all(),
        linked=LostReport.query.filter_by(linked_item_id=item.id).all(),
        claims=Claim.query.filter_by(item_id=item.id).order_by(Claim.created_at.desc()).all(),
        approved=Claim.query.filter_by(item_id=item.id, status="APPROVED", code_used_at=None).first(),
    )


@bp.route("/admin/items/<int:item_id>/photo")
@admin_required
def admin_item_photo(item_id):
    item = db.get_or_404(FoundItem, item_id)
    if not item.photo_path:
        abort(404)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], item.photo_path)


@bp.route("/admin/items/<int:item_id>/link", methods=["POST"])
@admin_required
def admin_link(item_id):
    item = db.get_or_404(FoundItem, item_id)
    report = db.session.get(LostReport, request.form.get("report_id", type=int) or 0)
    if report is None or report.linked_item_id is not None:
        flash("Choose a lost report that is not linked yet.", "error")
    else:
        report.linked_item_id = item.id  # S14
        notify(  # S15: only the student who filed the report
            report.student_id,
            f'A found item may match your lost report "{report.title}": '
            f'"{item.title}" ({item.category}, found {item.date_found:%d %b %Y}). '
            "Find it on the found-items list and submit a claim.",
        )
        db.session.commit()
        flash("Report linked and the student notified.")
    return redirect(url_for("main.admin_item", item_id=item.id))


@bp.route("/admin/claims/<int:claim_id>/approve", methods=["POST"])
@admin_required
def admin_approve(claim_id):
    claim = db.get_or_404(Claim, claim_id)
    if claim.status != "PENDING":
        flash("This claim was already reviewed.", "error")
    else:
        claim.status = "APPROVED"
        claim.pickup_code = f"{secrets.randbelow(10**6):06d}"  # S17
        notify(
            claim.student_id,
            f'Your claim on "{claim.item.title}" was approved. '
            "Your pickup code is on your Claims page. Bring it to the security office.",
        )
        db.session.commit()
        flash("Claim approved. The student can now see their pickup code.")
    return redirect(url_for("main.admin_item", item_id=claim.item_id))


@bp.route("/admin/claims/<int:claim_id>/reject", methods=["POST"])
@admin_required
def admin_reject(claim_id):
    claim = db.get_or_404(Claim, claim_id)
    if claim.status != "PENDING":
        flash("This claim was already reviewed.", "error")
    else:
        claim.status = "REJECTED"
        claim.item.status = "AVAILABLE"  # S18
        notify(claim.student_id, f'Your claim on "{claim.item.title}" was rejected.')
        db.session.commit()
        flash("Claim rejected. The item is available again.")
    return redirect(url_for("main.admin_item", item_id=claim.item_id))


@bp.route("/admin/items/<int:item_id>/handover", methods=["POST"])
@admin_required
def admin_handover(item_id):
    item = db.get_or_404(FoundItem, item_id)
    code = request.form.get("code", "").strip()
    claim = Claim.query.filter_by(item_id=item.id, status="APPROVED", code_used_at=None).first()
    if (
        item.status != "CLAIMED"
        or claim is None
        or not secrets.compare_digest(claim.pickup_code, code)
    ):
        flash("Wrong or already used pickup code.", "error")  # S19, S20
        return redirect(url_for("main.admin_item", item_id=item.id))

    claim.code_used_at = datetime.now()
    item.status = "RETURNED"
    db.session.add(  # S21
        Handover(item_id=item.id, student_id=claim.student_id, admin_id=current_user.id)
    )
    db.session.commit()
    flash(f"Item handed over to {claim.student.name}.")
    return redirect(url_for("main.admin_item", item_id=item.id))
