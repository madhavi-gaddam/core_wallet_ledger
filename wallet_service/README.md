# Wallet & Ledger Service

FastAPI wallet backend using your existing PostgreSQL schema:

- `users`: integer `id`, `username`, `email`, `created_at`
- `wallets`: integer `id`, `user_id`, `balance`, timestamps
- `ledger`: integer `id`, `user_id`, `wallet_id`, `transaction_type`, `amount`,
  `balance_before`, `balance_after`, `description`, `created_at`

Phase 2 adds concurrency safety without replacing those tables:

- Wallet rows are locked with `SELECT ... FOR UPDATE` during debit/credit.
- Wallet balance update and ledger insert happen in one DB transaction.
- Failed debits roll back and do not create ledger rows.
- `ledger.idempotency_key` is added to prevent duplicate retries.
- PostgreSQL constraints/indexes protect consistency across workers/instances.

## Run

```powershell
cd C:\Users\FL_LPT-694\Desktop\core_wallet_ledger
.\venv\Scripts\Activate.ps1
cd wallet_service
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

## Test Concurrency

```powershell
pytest tests/test_concurrent_debits.py -s
```

Expected:

```text
Concurrency result: successes=10, failures=40, final_balance=0.00, debit_ledger_count=10
1 passed
```

## curl Examples

Create user:

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username":"madhavi","email":"madhavi@example.com"}'
```

Create wallet:

```bash
curl -X POST http://localhost:8000/wallets \
  -H "Content-Type: application/json" \
  -d '{"user_id":1}'
```

Credit:

```bash
curl -X POST http://localhost:8000/wallets/1/credit \
  -H "Content-Type: application/json" \
  -d '{"amount":"100.00","idempotency_key":"credit-1","description":"Initial top up"}'
```

Debit:

```bash
curl -X POST http://localhost:8000/wallets/1/debit \
  -H "Content-Type: application/json" \
  -d '{"amount":"10.00","idempotency_key":"debit-1","description":"Purchase"}'
```

## Why It Works

Race conditions happen when concurrent requests read the same balance before any
of them commits. With `SELECT ... FOR UPDATE`, PostgreSQL serializes updates to
the same wallet row. Other requests wait, then see the latest committed balance.

Because the balance update and `ledger` insert are in the same transaction, the
system cannot commit one without the other. Since locking and uniqueness live in
PostgreSQL, this works across multiple FastAPI workers and multiple app
instances.
