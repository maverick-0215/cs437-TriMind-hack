# IITGN Lost & Found

Web app for the IITGN security office: admins log found items, students file lost reports, matches are scored, and the office approves an owner who collects the item with a one-time pickup code.

- **Backend:** Django + DRF + SQLite in `backend/`. Logic is in `backend/lostfound/` (`services.py` for matching, approval and handover; `views.py` for the API).
- **Frontend:** React + TypeScript + Vite in `frontend/src/`; admin pages in `pages/admin/`.
- **Run:** `cd backend && python manage.py runserver` (port 8000) and `cd frontend && npm run dev` (port 5173). Settings come from `backend/.env`.
- **Test:** `cd backend && pytest`; `cd frontend && npm test && npm run lint && npm run build`.
- **Spec:** `SPEC.md`, statements `S1`–`S32`. Every statement needs a backend test named `test_S<n>_...`; `backend/tests/test_spec_coverage.py` enforces it.

Rules:
- Never edit or delete an existing test to make the suite pass. Fix the code, or ask.
- Students must never see a found item's private fields (exact location, description, photo) - S7.
