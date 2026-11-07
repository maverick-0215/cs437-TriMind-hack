# IITGN Lost & Found

A web app for the lost and found service at IIT Gandhinagar. The security office lists the items it finds, students report what they have lost, and the app tells each student when a found item matches their report. It replaces the daily "lost and found" emails and trips to the security office just to check.

Built for CS437 (TriMind Hack), group G6.

## How it works

**Students**

1. File a lost report: what it is, when and where it was lost, and identifying details only the owner would know.
2. The report page lists found items that match it by 60% or more, with where each was found and who to meet. If nothing matches yet, the student is notified as soon as something does.
3. The student goes to the security office. The guard checks the identifying details and approves them in the app.
4. A 6-digit pickup code appears on the student's **Pickup codes** page. They tell it to the guard, collect the item, and the report shows **Closed**.

**Security office (admins)**

1. Add each found item. The exact location, description and photo stay private to admins.
2. On the item's page, see the students whose reports match, approve the right person, and enter their pickup code at handover.
3. Every handover is logged. Admins can add or remove other admins from the **Admins** page.

The full list of rules the app follows is in [SPEC.md](SPEC.md).

## Tech stack

- **Backend:** Python, Django, Django REST Framework, SQLite
- **Frontend:** React, TypeScript, Vite, React Router
- **Tests:** pytest (backend), Vitest and Testing Library (frontend)

## Project structure

```
backend/
  config/            Django settings and URLs
  lostfound/
    models.py        Found items, lost reports, approvals, handovers, notifications, admins
    services.py      Match scoring, approvals and handover logic
    views.py         API for students and admins
    auth_views.py    Sign-in: password, emailed codes, Google, dev login
    permissions.py   Who is an admin, who is a student
  tests/             One or more tests for every statement in SPEC.md
  startup.sh         Production start: migrations, then gunicorn
frontend/
  src/
    pages/           Student pages, plus admin/ for the security office
    App.tsx          Routes
    Layout.tsx       Header and navigation
    index.css        All styles
SPEC.md              What the app must do (S1 to S31)
.github/workflows/   Tests every push; deploys main to Azure
```

## Getting started

You need **Python 3.12+** and **Node.js 22.12+** (Node 24 recommended). Run the backend and frontend in two separate terminals.

### 1. Backend (http://localhost:8000)

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- macOS / Linux: `source .venv/bin/activate`

Then:

```bash
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
python manage.py migrate
python manage.py runserver
```

### 2. Frontend (http://localhost:5173)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

### 3. First sign-in

1. On the sign-in page, click **New here? Create a password** and enter your `@iitgn.ac.in` email.
2. Until email is set up (see below), the code is printed in the backend terminal. Copy it, choose a password, and sign in.
3. Choose **Sign in as admin** if your email is in `ADMIN_EMAILS`, otherwise **Sign in as student**.

## Configuration

Settings live in `backend/.env`. Start from `backend/.env.example`.

| Setting | What it does |
| --- | --- |
| `SECRET_KEY` | Signs login sessions. Required when `DEBUG=0`. Generate one with `python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"` |
| `DEBUG` | `1` while developing, `0` when the app is live. |
| `ADMIN_EMAILS` | Comma-separated permanent admins (the security office). More admins can be added in the app. |
| `SECURITY_CONTACT` | Shown to students next to matching items, for example the office location and phone number. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | The account that sends sign-up and forgot-password codes. Leave `EMAIL_HOST` empty to print emails in the backend terminal instead. |
| `GOOGLE_CLIENT_ID` | Optional. Adds a "Sign in with Google" button. Create a Web client ID in Google Cloud Console and add `http://localhost:5173` as an authorized JavaScript origin. |
| `DEV_LOGIN` | Development only. `1` lets anyone sign in by typing an email, with no password. Works only with `DEBUG=1`. Keep it `0` whenever other people can reach the app. |
| `CSRF_TRUSTED_ORIGINS` | The address the frontend is served from. Defaults to the Vite dev server. |
| `ALLOWED_HOSTS` | Domain names the site answers to. Defaults to `localhost`. |
| `DATA_DIR` | Folder for the database and photos. Defaults to `backend/`. Use `/home/data` on Azure. |

### Sending real email

For Gmail, use `EMAIL_HOST=smtp.gmail.com`, `EMAIL_PORT=587`, your Gmail address as `EMAIL_HOST_USER`, and an **App Password** (Google Account, Security, App passwords) as `EMAIL_HOST_PASSWORD`. An institute mail account works the same way with its own server details.

## Running the tests

```bash
cd backend && pytest
cd frontend && npm test
```

Every statement in [SPEC.md](SPEC.md) has at least one backend test whose name starts with its ID, for example `test_S17_...`. `tests/test_spec_coverage.py` fails if any statement has no test.

Other frontend checks:

```bash
npm run lint      # ESLint
npm run build     # type check and production build
```

## Before going live

- Set `DEBUG=0`, `DEV_LOGIN=0` and a long random `SECRET_KEY`.
- Set up real email so students receive their codes.
- On Azure, set `DATA_DIR=/home/data`, or the database is lost on every deploy.
- Put the real security office emails in `ADMIN_EMAILS` and the real contact details in `SECURITY_CONTACT`.
- Never commit `backend/.env`. It is already in `.gitignore`.
