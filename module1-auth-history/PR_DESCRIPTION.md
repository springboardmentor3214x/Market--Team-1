## Module 1: JWT Authentication and User-Specific Research History

### What this PR adds
- User registration and login (email or username) with bcrypt password hashing
- JWT access tokens (configurable expiry) and a reusable `get_current_user` dependency
- Research history CRUD scoped to the logged-in user, with pagination, search and market filter
- Pytest suite covering auth, token validation and user data isolation
- `.env.example`, `.gitignore`, `requirements.txt` and README with setup steps

### Endpoints
`POST /auth/register`, `POST /auth/login`, `POST /auth/login-json`, `GET /auth/me`,
`POST /history`, `GET /history`, `GET /history/{id}`, `DELETE /history/{id}`, `DELETE /history`

### How to test
1. `pip install -r requirements.txt`, copy `.env.example` to `.env` and set `SECRET_KEY`
2. `pytest -v`
3. `uvicorn app.main:app --reload` and try the endpoints at `/docs`

### Notes for reviewers
- Other modules can protect routes with `Depends(get_current_user)` from `app/deps.py`
- No secrets are committed; `.env` is git-ignored
- Branch: `feature/<your-name>` → `main`
