# CS437-TriMind-Hack

## G6: Lost and Found App

- App/Website for Lost and Found items recovery
	
- Current 
	- We receive daily mails listing items that are lost and found(often without photos)
	- We then go to respective security guards to recover the lost items

- What are the current issues and how can the webpage/app help
	- Many of us realize a few days later that something is lost and then go through the Lost and Found emails
	- We have to go and talk to the security guard just to check if the item is still there
	- Our app can help with the photos and live status of what all items are there with the security guards, this can serve as a single place to check for lost items and recover them instead of going through multiple emails(and also people get relief from daily spam of emails)
	- People can raise lost items tickets in the app itself instead of writing mails
	- We can have a search bar for categories of items lost(like umbrellas, watches, cycles etc)
	- Some additional security features

## Run it

The app has two parts: a Django API in `backend/` and a React + TypeScript site in `frontend/`. Needs Python 3.12+ and Node.js 20+.

**Backend** (http://localhost:8000):

```bash
cd backend
python -m venv .venv
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# macOS/Linux:          source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then fill it in (see below)
python manage.py migrate
python manage.py runserver
```

**Frontend** (http://localhost:5173, the address you open), in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

**Settings in `backend/.env`:**

- `ADMIN_EMAILS`: the security guards' emails. Everyone else who logs in is a student.
- `GOOGLE_CLIENT_ID`: login is "Sign in with Google", limited to `@iitgn.ac.in` accounts. Create a client ID in Google Cloud Console (APIs & Services → Credentials → OAuth client ID, type "Web application") and add `http://localhost:5173` under "Authorized JavaScript origins".
- `DEV_LOGIN=1` (development only, needs `DEBUG=1`): log in by typing any `@iitgn.ac.in` email, without Google. Use it to try the app before the client ID exists. Never turn it on for real use.
- `SECRET_KEY`: required unless `DEBUG=1`.

**Test:**

```bash
cd backend && pytest
cd frontend && npm test
```

What the app must do is listed in [SPEC.md](SPEC.md). Each statement (S1–S23) has backend tests in `backend/tests/` whose names start with its ID, and `test_spec_coverage.py` fails if any statement has none. The frontend tests in `frontend/src/routes.test.tsx` check the page-level rules (S3, S23).
