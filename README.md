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

Needs Python 3.11 or newer.

```bash
python -m venv .venv
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# macOS/Linux:          source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # set SECRET_KEY, and ADMIN_EMAILS to the guard's email
```

**Run:** `flask --app app run`, then open http://127.0.0.1:5000

**Test:** `pytest`

To use the app as an admin, sign up with an email that is listed in `ADMIN_EMAILS`. Every other `@iitgn.ac.in` account is a student.

What the app must do is listed in [SPEC.md](SPEC.md). Each statement (S1–S22) has tests in `tests/` whose names start with its ID.
