# IITGN Lost & Found (Group G6)

Django REST API in `backend/`, React + TypeScript (Vite) site in `frontend/`. Deployed on Azure App Service.

- Run: `cd backend && .venv/Scripts/python manage.py runserver` (macOS/Linux: `.venv/bin/python`), and in a second terminal `cd frontend && npm run dev`, then open http://localhost:5173. Needs `backend/.env` (copy `.env.example`).
- Test: `cd backend && .venv/Scripts/python -m pytest` and `cd frontend && npm test`
- Spec: `SPEC.md`, statements S1, S2, ... (not consecutive). Backend tests are named `test_S<n>_...` in `backend/tests/`; `test_spec_coverage.py` fails if a statement has no test.
- Code: rules in `backend/lostfound/services.py`, API in `views.py` and `auth_views.py`, pages in `frontend/src/pages/`.
- Deploy: merging to `main` runs `.github/workflows/azure-deploy.yml` (tests, then deploy). Keep `backend/startup.sh` with LF line endings.
- Never edit an existing test to make the suite pass. Never commit `backend/.env`.
- Students never see a found item's private details (exact location, description, photo).
