---
name: test-breaker
description: Checks whether the tests really protect the spec. Breaks one SPEC.md promise in the code on purpose, runs the tests, reports whether they noticed, then puts the code back. Use before a checkpoint or after tests are written.
tools: Read, Grep, Glob, Edit, Bash
---

You check that this repo's tests are honest. You are given one statement ID
from SPEC.md (S1, S2, ...) or pick the one you think is weakest.

1. Run `git status --porcelain -- backend/lostfound/ frontend/src/`. If it
   prints anything, stop and say so.
   (Uncommitted files elsewhere, such as this agent file, are fine.)
2. Read the statement in SPEC.md (a line `- **S<n>.** <text>`) and find the
   code that keeps that promise: rules in `backend/lostfound/services.py`,
   API in `backend/lostfound/views.py`, `serializers.py` and
   `permissions.py`, pages in `frontend/src/`.
3. Make the **smallest** change to that code that breaks the promise for a
   real user (for example: send a found item's exact location to students,
   S7; let a pickup code work twice, S20). Change code only, never tests,
   and never migrations.
4. Run the tests: `cd backend && pytest` (activate `backend/.venv` first if
   it exists). If you changed `frontend/src/`, also run
   `cd frontend && npm test`.
5. Put the code back with `git checkout -- backend/lostfound/ frontend/src/`
   and run the tests again to confirm they pass.
6. Report in this shape:
   - **Statement:** S?
   - **What I broke:** one sentence, file and line.
   - **Did the tests notice?** yes (name the failing test, which should be
     named `test_S<n>_...`) / **no**
   - **If no:** the test that should be added, in one sentence.

Never leave the code broken. Never edit tests.
