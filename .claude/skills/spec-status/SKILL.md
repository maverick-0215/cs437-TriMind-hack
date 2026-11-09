---
name: spec-status
description: Report which SPEC.md statements have tests and whether they pass. Use when asked about spec status, test coverage of the spec, or what to work on next.
---

Report only. Do not edit code, tests or SPEC.md, and do not fix failures.

1. Read `SPEC.md`. Each statement is a line `- **S<n>.** <text>`. List every ID with a short version of its text, in the order they appear.
2. Find each statement's tests by name:
   - Backend: `backend/tests/test_*.py`, functions named `test_S<n>_...`. One test can cover several IDs, e.g. `test_S3_S23_...`.
   - Frontend: `frontend/src/**/*.test.tsx`, `describe`/`it` titles starting with the ID, e.g. `'S29, S30: ...'`.
3. Run each suite once and keep the per-test results:
   - Backend: `cd backend && pytest -v` (activate `backend/.venv` first if it exists).
   - Frontend: `cd frontend && npx vitest run --reporter=verbose`.
4. Print one table, in SPEC order:

   | ID | Statement | Tests | Result |
   |---|---|---|---|

   Tests: count per suite, e.g. `3 backend, 1 frontend`. Result: `green` if all its tests pass, `red` if any fail (name the failing tests under the table), `no test` if none were found.
5. End with the counts (green / red / no test) and the next statement to work on: the first red one, else the first with no test, else say all statements are green.
