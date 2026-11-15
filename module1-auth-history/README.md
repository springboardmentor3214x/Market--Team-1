# Module 1 – User Authentication & Research History

FastAPI backend: user registration/login, JWT authentication, and user-specific research history.

## Project structure
```
module1-auth-history/
├── app/
│   ├── main.py          # FastAPI app, CORS, router registration
│   ├── config.py        # settings from .env
│   ├── database.py      # SQLAlchemy engine/session
│   ├── models.py        # User, ResearchHistory
│   ├── schemas.py       # request/response validation
│   ├── security.py      # bcrypt hashing + JWT create/verify
│   ├── deps.py          # get_current_user (reuse in other modules)
│   └── routers/
│       ├── auth.py      # /auth/register, /auth/login, /auth/login-json, /auth/me
│       └── history.py   # /history CRUD (scoped to logged-in user)
├── tests/               # pytest suite
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup
```bash
python -m venv venv
venv\Scripts\activate            # Windows (PowerShell)  |  source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
copy .env.example .env           # Mac/Linux: cp .env.example .env
```
Open `.env` and set `SECRET_KEY`. Generate one with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Run
```bash
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs, register, click **Authorize**, log in, and try the `/history` endpoints.

## Run tests
```bash
pytest -v
```

## API summary
| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/register` | No | Create account (email, username, password) |
| POST | `/auth/login` | No | Form login (email or username) → JWT |
| POST | `/auth/login-json` | No | JSON login `{identifier, password}` → JWT |
| GET | `/auth/me` | Yes | Current user |
| POST | `/history` | Yes | Save a research entry |
| GET | `/history` | Yes | List own entries (`page`, `page_size`, `q`, `market`) |
| GET | `/history/{id}` | Yes | Get one own entry |
| DELETE | `/history/{id}` | Yes | Delete one own entry |
| DELETE | `/history` | Yes | Clear all own history |

Send the token as `Authorization: Bearer <token>`.

### Example (curl)
```bash
curl -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","username":"me","password":"Passw0rd123"}'

curl -X POST http://127.0.0.1:8000/auth/login-json -H "Content-Type: application/json" \
  -d '{"identifier":"me","password":"Passw0rd123"}'

curl -X POST http://127.0.0.1:8000/history -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"Analyze the EV market in India","market":"India","analysis_period":"1Y","result_summary":"..."}'
```

### Frontend (React) snippet
```js
const res = await fetch("http://127.0.0.1:8000/auth/login-json", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ identifier, password }),
});
const { access_token } = await res.json();
// then on every request:
fetch("http://127.0.0.1:8000/history", { headers: { Authorization: `Bearer ${access_token}` } });
```

## For teammates (integration)
Protect any route with the logged-in user:
```python
from fastapi import Depends
from app.deps import get_current_user
from app.models import User

@router.get("/watchlist")
def my_watchlist(current_user: User = Depends(get_current_user)):
    ...  # filter data by current_user.id
```
To save an agent's analysis into a user's history, insert a `ResearchHistory(user_id=..., query=..., result_summary=..., result_data=...)` row or call `POST /history`.

## Security notes
- Passwords are hashed with bcrypt; plain passwords are never stored.
- JWT is signed (HS256) with `SECRET_KEY` and expires (default 60 min).
- History queries always filter by the user id from the verified token; other users' entries return 404.
- `.env` and `*.db` are git-ignored. Never commit secrets.
