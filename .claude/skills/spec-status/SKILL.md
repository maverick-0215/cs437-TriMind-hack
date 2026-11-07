---
name: spec-status
description: Report which SPEC.md statements are green, red, or untested in this repo. Use when someone asks "where are we", "what is left", "is the spec green", or before opening a pull request.
---

# Spec status

1. Read `SPEC.md`. List every statement ID with its one-line title. IDs look like
   `**S17.**`; they are not consecutive (some numbers were retired), so list only the ones
   that are there, in the order they appear.
2. Find the tests for each statement. In this repo:
   - **Backend** (`backend/tests/test_*.py`): a test belongs to a statement when its
     function name starts with `test_S<n>_` (for example `test_S19_wrong_code_is_rejected...`).
     One statement can have tests in several files.
   - **Frontend** (`frontend/src/routes.test.tsx`): a test belongs to a statement when its
     `describe(...)` or `it(...)` name mentions the ID, e.g. `'S3: students get 403...'`
     or `'S29, S30: password sign-in...'` (that one counts for both).
   - `backend/tests/test_spec_coverage.py` checks every statement has a test; it belongs
     to no single statement.
3. Run both suites once, verbose, so each test's name and result is printed:
   - Backend, from `backend/` with its virtualenv:
     `.venv/Scripts/python -m pytest -v` (Windows) or `.venv/bin/python -m pytest -v`
     (macOS/Linux).
   - Frontend, from `frontend/`: `npm test -- --reporter=verbose`
4. Print one table, nothing else before it:

   | ID | Statement | Tests | Result |
   |----|-----------|-------|--------|

   *Tests* is the number of backend + frontend tests for that statement, e.g. `3 + 1`.
   Result is **green** (all its tests pass), **red** (any test fails, give the
   first line of the failure), or **no test**.
5. Under the table, at most three lines: the count of green / red / no test, the
   total tests passed in each suite, and the one statement to work on next (the first
   red, else the first untested; if everything is green, say so).

Do not edit any file. Do not fix anything. This skill only reports.
