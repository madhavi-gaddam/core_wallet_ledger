# Setup Guide - Core Wallet & Ledger (Phase 1)

## Quick Start - Windows

### Step 1: Activate Virtual Environment

```bash
cd c:\Users\FL_LPT-694\Desktop\core_wallet_ledger
venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Setup PostgreSQL Database

#### Option A: Using PostgreSQL GUI (pgAdmin)

1. Open pgAdmin or connect to PostgreSQL
2. Create new database: `core_wallet_db`
3. Note your connection details (username, password, host, port)

#### Option B: Using Command Line

```bash
# Windows Command Prompt
createdb -U postgres core_wallet_db

# Or with psql shell
psql -U postgres
CREATE DATABASE core_wallet_db;
\q
```

### Step 4: Configure Environment

1. Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

2. Edit `.env` with your database credentials:

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/core_wallet_db
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-change-this
```

Replace:
- `postgres` → your PostgreSQL username
- `password` → your PostgreSQL password
- `localhost` → your database host
- `5432` → your database port (default is 5432)

### Step 5: Initialize Database

```bash
# Create all tables
flask --app run init-db
```

You should see: `Database initialized!`

### Step 6: Run the Application

```bash
python run.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

## Testing the API

### Option 1: Using cURL (Command Line)

Open a new terminal (keep Flask running) and test endpoints:

```bash
# Test 1: Create User
curl -X POST http://localhost:5000/api/wallet/create-user ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"john\", \"email\": \"john@example.com\"}"

# Test 2: Credit Wallet (change user_id as needed)
curl -X POST http://localhost:5000/api/wallet/credit ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\": 1, \"amount\": 1000, \"description\": \"Salary\"}"

# Test 3: Get Balance
curl http://localhost:5000/api/wallet/balance/1

# Test 4: Debit Wallet
curl -X POST http://localhost:5000/api/wallet/debit ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\": 1, \"amount\": 250, \"description\": \"Payment\"}"

# Test 5: Get Transaction History
curl http://localhost:5000/api/wallet/history/1

# Test 6: Get User Info
curl http://localhost:5000/api/wallet/user/1
```

### Option 2: Using Postman

1. Download [Postman](https://www.postman.com/downloads/)
2. Import requests (or create manually):

| Method | URL | Body |
|--------|-----|------|
| POST | `http://localhost:5000/api/wallet/create-user` | `{"username": "john", "email": "john@example.com"}` |
| POST | `http://localhost:5000/api/wallet/credit` | `{"user_id": 1, "amount": 1000, "description": "Salary"}` |
| GET | `http://localhost:5000/api/wallet/balance/1` | - |
| POST | `http://localhost:5000/api/wallet/debit` | `{"user_id": 1, "amount": 250, "description": "Payment"}` |
| GET | `http://localhost:5000/api/wallet/history/1` | - |
| GET | `http://localhost:5000/api/wallet/user/1` | - |

### Option 3: Using Python Test Script

```bash
python test_wallet.py
```

This runs in-memory tests without needing PostgreSQL.

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'flask'`

**Solution:** Make sure virtual environment is activated:
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: `psycopg2.OperationalError: could not connect to server`

**Solution:** Check your `.env` file database URL:
- Verify PostgreSQL is running
- Check username, password, host, port
- Verify database `core_wallet_db` exists

```bash
# Test connection
psql -U postgres -h localhost -d core_wallet_db
```

### Issue: `flask: command not found`

**Solution:** Reinstall Flask:
```bash
pip install flask --upgrade
```

### Issue: Database already exists error

**Solution:** Drop and recreate:
```bash
# In psql shell
DROP DATABASE core_wallet_db;
CREATE DATABASE core_wallet_db;
```

Or use Flask commands:
```bash
flask --app run drop-db
flask --app run init-db
```

## Project Structure

```
core_wallet_ledger/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # User, Wallet, Ledger models
│   ├── routes.py            # API endpoints
│   └── services.py          # Business logic & validation
├── config/
│   ├── __init__.py
│   └── config.py            # Configuration management
├── migrations/              # Future: Database migrations
├── tests/                   # Unit tests directory
├── .env.example             # Environment template
├── .gitignore              # Git ignore rules
├── requirements.txt         # Python dependencies
├── run.py                   # Flask entry point
├── test_wallet.py          # Test script
├── README.md               # API documentation
└── SETUP.md                # This file
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Wallets Table
```sql
CREATE TABLE wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    balance NUMERIC(15,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Ledger Table (Transaction History)
```sql
CREATE TABLE ledger (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    wallet_id INTEGER NOT NULL REFERENCES wallets(id),
    transaction_type VARCHAR(10) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    balance_before NUMERIC(15,2) NOT NULL,
    balance_after NUMERIC(15,2) NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Key Features Implemented

✅ **Create User & Wallet** - One wallet per user  
✅ **Credit Operations** - Add funds with validation  
✅ **Debit Operations** - Withdraw funds with balance check  
✅ **Negative Balance Prevention** - Cannot debit more than balance  
✅ **Transaction Ledger** - Complete audit trail  
✅ **Decimal Precision** - Use Decimal for financial accuracy  
✅ **PostgreSQL Persistence** - All data persisted  
✅ **RESTful API** - Clean JSON endpoints  
✅ **Error Handling** - Comprehensive validation  
✅ **Service Layer** - Business logic separated  

## Next Steps

After Phase 1 is working:

- **Phase 2:** Add JWT authentication
- **Phase 3:** Add transaction fees
- **Phase 4:** Add recurring transactions
- **Phase 5:** Add multi-currency support
- **Phase 6:** Add rate limiting & monitoring

## Support

For issues or questions, check:
1. `.env` configuration
2. PostgreSQL connection
3. Database tables created (`flask --app run init-db`)
4. Virtual environment activated

Good luck! 🚀
