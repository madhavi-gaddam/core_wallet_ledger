# Wallet & Ledger Service

Production-ready Phase 1 backend for a wallet and ledger system built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, and Pydantic.

## Features

- Create users
- Create one wallet per user
- Credit money to a wallet
- Debit money from a wallet
- Prevent negative balances
- Create a ledger entry for every credit and debit
- Read wallet balance
- Read transaction history sorted latest first
- Persist all data in PostgreSQL
- Use UUID primary keys, Decimal money values, timestamps, service layer, repository layer, and reusable exception handling

## Project Structure

```text
wallet_service/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── config.py
│   ├── models/
│   ├── schemas/
│   ├── routes/
│   ├── services/
│   ├── repositories/
│   ├── core/
│   └── utils/
├── alembic/
├── requirements.txt
├── .env
├── README.md
└── alembic.ini
```

## PostgreSQL Setup

Open PowerShell and run:

```powershell
psql -U postgres -c "CREATE DATABASE wallet_service_db;"
```

If the database already exists, use:

```powershell
psql -U postgres -c "DROP DATABASE IF EXISTS wallet_service_db;"
psql -U postgres -c "CREATE DATABASE wallet_service_db;"
```

The `.env` file is already configured as:

```env
DATABASE_URL=postgresql://postgres:Madhavi%4002@localhost:5432/wallet_service_db
APP_ENV=development
APP_DEBUG=True
```

The password contains `@`, so it is encoded as `%40` in the database URL.

## Install Dependencies

From the repository root:

```powershell
cd wallet_service
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run Migrations

```powershell
alembic upgrade head
```

This creates:

- `users`
- `wallets`
- `ledger_entries`
- PostgreSQL enum `transaction_type`

## Start Server

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

## API Endpoints

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### 1. Create User

```http
POST /users
```

Request:

```json
{
  "name": "Madhavi",
  "email": "madhavi@example.com"
}
```

Response:

```json
{
  "id": "8d0f1d9a-3951-45c1-ae9f-e9f0cc02f997",
  "name": "Madhavi",
  "email": "madhavi@example.com",
  "created_at": "2026-05-25T06:45:00.000000Z"
}
```

### 2. Create Wallet

```http
POST /wallets
```

Request:

```json
{
  "user_id": "8d0f1d9a-3951-45c1-ae9f-e9f0cc02f997"
}
```

Response:

```json
{
  "id": "bc0abbee-0663-4712-8d8b-18892fe6b655",
  "user_id": "8d0f1d9a-3951-45c1-ae9f-e9f0cc02f997",
  "balance": "0.00",
  "created_at": "2026-05-25T06:46:00.000000Z"
}
```

### 3. Credit Wallet

```http
POST /wallets/{wallet_id}/credit
```

Request:

```json
{
  "amount": 500,
  "description": "Added money"
}
```

Response:

```json
{
  "wallet_id": "bc0abbee-0663-4712-8d8b-18892fe6b655",
  "balance": "500.00",
  "ledger_entry_id": "190d2c55-3843-43c2-9c1e-67d73c43f725"
}
```

### 4. Debit Wallet

```http
POST /wallets/{wallet_id}/debit
```

Request:

```json
{
  "amount": 200,
  "description": "Purchase"
}
```

Response:

```json
{
  "wallet_id": "bc0abbee-0663-4712-8d8b-18892fe6b655",
  "balance": "300.00",
  "ledger_entry_id": "32d03434-af9a-422f-a2f3-907df6b4bbda"
}
```

Insufficient balance response:

```json
{
  "detail": "Insufficient wallet balance.",
  "error_code": "insufficient_funds"
}
```

### 5. Get Wallet Balance

```http
GET /wallets/{wallet_id}/balance
```

Response:

```json
{
  "wallet_id": "bc0abbee-0663-4712-8d8b-18892fe6b655",
  "balance": "300.00"
}
```

### 6. Get Transaction History

```http
GET /wallets/{wallet_id}/transactions
```

Response:

```json
[
  {
    "id": "32d03434-af9a-422f-a2f3-907df6b4bbda",
    "wallet_id": "bc0abbee-0663-4712-8d8b-18892fe6b655",
    "transaction_type": "DEBIT",
    "amount": "200.00",
    "balance_after_transaction": "300.00",
    "description": "Purchase",
    "created_at": "2026-05-25T06:49:00.000000Z"
  },
  {
    "id": "190d2c55-3843-43c2-9c1e-67d73c43f725",
    "wallet_id": "bc0abbee-0663-4712-8d8b-18892fe6b655",
    "transaction_type": "CREDIT",
    "amount": "500.00",
    "balance_after_transaction": "500.00",
    "description": "Added money",
    "created_at": "2026-05-25T06:48:00.000000Z"
  }
]
```

## PowerShell API Examples

```powershell
$user = Invoke-RestMethod -Method Post -Uri http://localhost:8000/users `
  -ContentType "application/json" `
  -Body '{"name":"Madhavi","email":"madhavi@example.com"}'

$wallet = Invoke-RestMethod -Method Post -Uri http://localhost:8000/wallets `
  -ContentType "application/json" `
  -Body (@{ user_id = $user.id } | ConvertTo-Json)

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/wallets/$($wallet.id)/credit" `
  -ContentType "application/json" `
  -Body '{"amount":500,"description":"Added money"}'

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/wallets/$($wallet.id)/debit" `
  -ContentType "application/json" `
  -Body '{"amount":200,"description":"Purchase"}'

Invoke-RestMethod -Method Get -Uri "http://localhost:8000/wallets/$($wallet.id)/balance"
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/wallets/$($wallet.id)/transactions"
```

## Notes

- Money is stored as `NUMERIC(18, 2)` and handled in Python as `Decimal`.
- Wallet updates use `SELECT FOR UPDATE` to protect balance changes during concurrent requests.
- Alembic is the source of truth for schema creation. Avoid calling `Base.metadata.create_all()` in production.
