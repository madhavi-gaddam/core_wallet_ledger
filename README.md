# Core Wallet & Ledger

A Python + PostgreSQL backend service for managing user wallets and transaction ledgers.

## Phase 1 Requirements

✅ Create a wallet for a user  
✅ Credit money to wallet  
✅ Debit money from wallet  
✅ Get wallet balance  
✅ Get transaction history (ledger)  

### Rules
- Every credit/debit creates a ledger entry
- Balance never goes negative
- Data stored in PostgreSQL (no in-memory state)

## Project Structure

```
core_wallet_ledger/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models (User, Wallet, Ledger)
│   ├── routes.py            # API endpoints
│   └── services.py          # Business logic (WalletService)
├── config/
│   └── config.py            # Configuration management
├── migrations/              # Alembic migrations (future)
├── tests/                   # Unit tests
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
├── run.py                   # Flask application entry point
└── README.md                # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and update database credentials:

```
DATABASE_URL=postgresql://username:password@localhost:5432/core_wallet_db
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
```

### 5. Create Database

```bash
# Using psql
createdb core_wallet_db

# Or via PostgreSQL GUI
```

### 6. Initialize Database Tables

```bash
flask --app run init-db
```

### 7. Run the Application

```bash
python run.py
```

The API will be available at `http://localhost:5000/`

## API Endpoints

### Create User & Wallet
**POST** `/api/wallet/create-user`

```json
{
  "username": "john_doe",
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "message": "User and wallet created successfully",
  "user_id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "wallet_id": 1,
  "balance": "0.00"
}
```

### Credit Wallet
**POST** `/api/wallet/credit`

```json
{
  "user_id": 1,
  "amount": 100.50,
  "description": "Salary deposit"
}
```

**Response:**
```json
{
  "message": "Credit successful",
  "transaction_id": 1,
  "amount": "100.50",
  "balance_after": "100.50",
  "timestamp": "2026-05-25T10:30:00"
}
```

### Debit Wallet
**POST** `/api/wallet/debit`

```json
{
  "user_id": 1,
  "amount": 25.00,
  "description": "Payment for services"
}
```

**Response:**
```json
{
  "message": "Debit successful",
  "transaction_id": 2,
  "amount": "25.00",
  "balance_after": "75.50",
  "timestamp": "2026-05-25T10:35:00"
}
```

### Get Balance
**GET** `/api/wallet/balance/<user_id>`

**Response:**
```json
{
  "user_id": 1,
  "balance": "75.50"
}
```

### Get Transaction History
**GET** `/api/wallet/history/<user_id>?limit=10&offset=0`

**Response:**
```json
{
  "user_id": 1,
  "transaction_count": 2,
  "transactions": [
    {
      "transaction_id": 2,
      "type": "DEBIT",
      "amount": "25.00",
      "balance_before": "100.50",
      "balance_after": "75.50",
      "description": "Payment for services",
      "timestamp": "2026-05-25T10:35:00"
    },
    {
      "transaction_id": 1,
      "type": "CREDIT",
      "amount": "100.50",
      "balance_before": "0.00",
      "balance_after": "100.50",
      "description": "Salary deposit",
      "timestamp": "2026-05-25T10:30:00"
    }
  ]
}
```

### Get User Info
**GET** `/api/wallet/user/<user_id>`

**Response:**
```json
{
  "user_id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "balance": "75.50",
  "created_at": "2026-05-25T10:25:00"
}
```

## Testing

Run tests:

```bash
pytest tests/ -v
```

Run tests with coverage:

```bash
pytest tests/ --cov=app
```

## Database Models

### User
- `id` (PK)
- `username` (unique)
- `email` (unique)
- `created_at`

### Wallet
- `id` (PK)
- `user_id` (FK, unique)
- `balance` (Decimal)
- `created_at`
- `updated_at`

### Ledger
- `id` (PK)
- `user_id` (FK)
- `wallet_id` (FK)
- `transaction_type` (CREDIT/DEBIT)
- `amount` (Decimal)
- `balance_before` (Decimal)
- `balance_after` (Decimal)
- `description`
- `created_at`

## Features

- ✅ User management
- ✅ Wallet creation per user
- ✅ Credit/Debit operations with validation
- ✅ Complete transaction ledger
- ✅ Negative balance prevention
- ✅ PostgreSQL persistence
- ✅ RESTful API endpoints
- ✅ Error handling & validation

## Next Steps (Future Phases)

- Phase 2: User authentication & authorization
- Phase 3: Transaction fees & interest calculations
- Phase 4: Scheduled transactions & recurring payments
- Phase 5: Multi-currency support
- Phase 6: API rate limiting & monitoring
