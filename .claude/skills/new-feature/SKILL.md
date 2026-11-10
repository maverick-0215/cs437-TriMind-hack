---
name: new-feature
description: Turn a plain-English feature request into a new SPEC.md statement, a failing test, and the code that makes it pass. Use when a user or the acceptance run asks for a new feature.
---

# New feature, spec first

Work in this order. Do not skip ahead.

0. **Branch.** Find the next free statement ID: the highest `**S<n>.**` in
   `SPEC.md` plus one (IDs are not in order in the file, so check them all).
   Check `git status`; if there are uncommitted changes, stop and say so.
   Then create and switch to `feature/S<n>-<short-name>` before touching any file.
1. **Restate.** Write the request back as one checkable sentence, in the
   style of the existing statements in `SPEC.md` (`- **S<n>.** <text>`).
   If it is ambiguous, or it would break an existing statement (for example
   S7: students never see a found item's private fields), ask one question
   and stop.
2. **Spec.** Add it to `SPEC.md` as `- **S<n>.** <text>` under the section
   it fits (Access, Found items, Lost reports, Matching, Approval and
   handover, Records). Below it add an indented line
   `*Test:* <how it will be checked>`.
3. **Failing test.** Add a backend test named `test_S<n>_<what_it_checks>`
   in the matching file in `backend/tests/` (`test_access.py`,
   `test_found_items.py`, `test_lost_reports.py`, `test_matching.py`,
   `test_claims.py`, `test_admins.py`). Reuse the fixtures in
   `backend/tests/conftest.py`. If the feature is only visible in the UI,
   also add a frontend test in `frontend/src/**/*.test.tsx` whose `it`
   title starts with `S<n>:`.
   Run `cd backend && pytest` (activate `backend/.venv` first if it exists).
   Show that the new test fails and every old test still passes. If the new
   test passes already, the test is wrong: fix the test, not the code.
4. **Code.** Change the smallest amount of code that makes it pass: rules in
   `backend/lostfound/services.py`, API in `backend/lostfound/views.py`
   (and `serializers.py`, `models.py` with a migration if needed), pages in
   `frontend/src/`.
5. **Check.** Run the full suites: `cd backend && pytest`, and if you
   touched the frontend, `cd frontend && npm test && npm run lint && npm run build`.
   Then run the `spec-status` skill.
6. **Commit** on that branch, one commit, message `S<n>: <statement>`. Do not
   push and do not merge: a teammate reviews the pull request.

Never edit or delete an existing test to make the suite pass.
