# Wallet & Ledger Service

FastAPI wallet backend using PostgreSQL, SQLAlchemy, Alembic, Pydantic, JWT,
and bcrypt password hashing.

Current security and consistency features:

- JWT registration/login with expiring Bearer tokens.
- Passwords are stored as bcrypt hashes, never plain text.
- All `/wallets` APIs require authentication.
- Wallet reads/writes are authorized by `wallet.user_id`.
- Clients cannot choose `user_id` when creating a wallet.
- Wallet rows are locked with `SELECT ... FOR UPDATE` during debit/credit.
- Balance update and ledger insert happen in one DB transaction.
- Failed debits roll back and do not create ledger rows.
- `ledger.idempotency_key` prevents duplicate retries.

## Environment

Set these in `.env` or the shell:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/wallet_service_db
APP_ENV=development
APP_DEBUG=True
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:8000
ALLOWED_HOSTS=localhost,127.0.0.1
DOCS_ENABLED=True
```

For production:

```env
APP_ENV=production
APP_DEBUG=False
SECRET_KEY=use-at-least-32-random-characters
DOCS_ENABLED=False
ALLOWED_HOSTS=api.example.com
ALLOWED_ORIGINS=https://app.example.com
```

The application refuses to start in production with the default JWT secret or
with debug mode enabled.

## Run

```powershell
cd C:\Users\FL_LPT-694\Desktop\core_wallet_ledger
.\venv\Scripts\Activate.ps1
cd wallet_service
python -m pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

Health endpoints:

```text
GET /health
GET /ready
```

## Tests

```powershell
cd C:\Users\FL_LPT-694\Desktop\core_wallet_ledger\wallet_service
..\venv\Scripts\python.exe -m pytest tests/test_concurrent_debits.py -s
```

Expected:

```text
Concurrency result: successes=10, failures=40, final_balance=0.00, debit_ledger_count=10
8 passed
```

## API Examples

Register:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"madhavi","password":"StrongPass123"}'
```

Login:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"madhavi","password":"StrongPass123"}'
```

Response:

```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

Create wallet for the authenticated user:

```bash
curl -X POST http://localhost:8000/wallets \
  -H "Authorization: Bearer jwt_token_here" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Credit:

```bash
curl -X POST http://localhost:8000/wallets/1/credit \
  -H "Authorization: Bearer jwt_token_here" \
  -H "Content-Type: application/json" \
  -d '{"amount":"100.00","idempotency_key":"credit-1","description":"Initial top up"}'
```

Debit:

```bash
curl -X POST http://localhost:8000/wallets/1/debit \
  -H "Authorization: Bearer jwt_token_here" \
  -H "Content-Type: application/json" \
  -d '{"amount":"10.00","idempotency_key":"debit-1","description":"Purchase"}'
```

Unauthorized request without a token:

```json
{
  "detail": "Authentication token is required.",
  "error_code": "unauthorized"
}
```

Forbidden request when accessing another user's wallet:

```json
{
  "detail": "You are not allowed to access this wallet.",
  "error_code": "forbidden"
}
```

## Why It Works

Authentication proves who the caller is through a signed JWT. Authorization is
enforced by querying wallets with both `wallet.id` and `wallet.user_id`; the API
never trusts a client-provided user ID.

Race conditions happen when concurrent requests read the same balance before any
of them commits. With `SELECT ... FOR UPDATE`, PostgreSQL serializes updates to
the same wallet row. Other requests wait, then see the latest committed balance.

Because the balance update and `ledger` insert are in the same transaction, the
system cannot commit one without the other. Since locking and uniqueness live in
PostgreSQL, this works across multiple FastAPI workers and app instances.
