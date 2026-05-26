import asyncio
import uuid
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import func, select

from app.config import get_settings
from app.database import SessionLocal
from app.main import app
from app.models.ledger_entry import LedgerEntry, TransactionType
from app.models.wallet import Wallet


async def register_and_login(client: AsyncClient, username_prefix: str = "test"):
    username = f"{username_prefix}_{uuid.uuid4().hex[:12]}"
    password = "StrongPass123"
    register_response = await client.post(
        "/auth/register",
        json={
            "username": username,
            "password": password,
        },
    )
    assert register_response.status_code == 201, register_response.text

    login_response = await client.post(
        "/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]
    return register_response.json(), {"Authorization": f"Bearer {token}"}


async def create_test_wallet(client: AsyncClient, balance: Decimal) -> tuple[int, dict]:
    _user, headers = await register_and_login(client)

    wallet_response = await client.post(
        "/wallets",
        json={},
        headers=headers,
    )
    assert wallet_response.status_code == 201, wallet_response.text
    wallet_id = int(wallet_response.json()["id"])

    with SessionLocal() as db:
        with db.begin():
            wallet = db.get(Wallet, wallet_id)
            assert wallet is not None
            wallet.balance = balance

    return wallet_id, headers


@pytest.mark.asyncio
async def test_50_concurrent_debits_only_10_succeed() -> None:
    """Integration test for PostgreSQL row locks and atomic ledger writes."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        wallet_id, headers = await create_test_wallet(client, Decimal("100.00"))

        async def debit_once(index: int):
            return await client.post(
                f"/wallets/{wallet_id}/debit",
                headers=headers,
                json={
                    "amount": "10.00",
                    "idempotency_key": f"debit-{wallet_id}-{index}",
                    "description": "concurrency stress debit",
                },
            )

        responses = await asyncio.gather(*(debit_once(i) for i in range(50)))

    successes = [response for response in responses if response.status_code == 200]
    failures = [response for response in responses if response.status_code != 200]

    with SessionLocal() as db:
        wallet = db.get(Wallet, wallet_id)
        ledger_count = db.scalar(
            select(func.count(LedgerEntry.id)).where(
                LedgerEntry.wallet_id == wallet_id,
                LedgerEntry.transaction_type == TransactionType.DEBIT,
            )
        )

    assert wallet is not None
    assert len(successes) == 10
    assert len(failures) == 40
    assert wallet.balance == Decimal("0.00")
    assert ledger_count == 10

    print(
        "\nConcurrency result: "
        f"successes={len(successes)}, failures={len(failures)}, "
        f"final_balance={wallet.balance}, debit_ledger_count={ledger_count}"
    )


@pytest.mark.asyncio
async def test_idempotent_debit_retry_does_not_double_charge() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        wallet_id, headers = await create_test_wallet(client, Decimal("100.00"))
        payload = {
            "amount": "10.00",
            "idempotency_key": f"retry-{wallet_id}",
            "description": "retry debit",
        }

        first = await client.post(
            f"/wallets/{wallet_id}/debit",
            json=payload,
            headers=headers,
        )
        second = await client.post(
            f"/wallets/{wallet_id}/debit",
            json=payload,
            headers=headers,
        )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["transaction_id"] == second.json()["transaction_id"]

    with SessionLocal() as db:
        wallet = db.get(Wallet, wallet_id)
        ledger_count = db.scalar(
            select(func.count(LedgerEntry.id)).where(
                LedgerEntry.wallet_id == wallet_id,
                LedgerEntry.transaction_type == TransactionType.DEBIT,
            )
        )

    assert wallet is not None
    assert wallet.balance == Decimal("90.00")
    assert ledger_count == 1


@pytest.mark.asyncio
async def test_failed_debit_does_not_create_ledger_entry() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        wallet_id, headers = await create_test_wallet(client, Decimal("5.00"))
        response = await client.post(
            f"/wallets/{wallet_id}/debit",
            headers=headers,
            json={
                "amount": "10.00",
                "idempotency_key": f"too-much-{wallet_id}",
                "description": "should fail",
            },
        )

    assert response.status_code == 400, response.text

    with SessionLocal() as db:
        wallet = db.get(Wallet, wallet_id)
        ledger_count = db.scalar(
            select(func.count(LedgerEntry.id)).where(
                LedgerEntry.wallet_id == wallet_id,
                LedgerEntry.transaction_type == TransactionType.DEBIT,
            )
        )

    assert wallet is not None
    assert wallet.balance == Decimal("5.00")
    assert ledger_count == 0


@pytest.mark.asyncio
async def test_login_rejects_invalid_password() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        user, _headers = await register_and_login(client, "bad_password")
        response = await client.post(
            "/auth/login",
            json={"username": user["username"], "password": "WrongPass123"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wallet_endpoint_requires_token() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/wallets", json={})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_is_rejected() -> None:
    settings = get_settings()
    expired_token = jwt.encode(
        {"sub": "1", "exp": 0},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/wallets",
            json={},
            headers={"Authorization": f"Bearer {expired_token}"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_cannot_access_another_users_wallet() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        wallet_id, _owner_headers = await create_test_wallet(client, Decimal("25.00"))
        _other_user, other_headers = await register_and_login(client, "other")

        balance_response = await client.get(
            f"/wallets/{wallet_id}/balance",
            headers=other_headers,
        )
        debit_response = await client.post(
            f"/wallets/{wallet_id}/debit",
            headers=other_headers,
            json={
                "amount": "1.00",
                "idempotency_key": f"forbidden-{wallet_id}",
            },
        )

    assert balance_response.status_code == 403
    assert debit_response.status_code == 403


@pytest.mark.asyncio
async def test_authenticated_user_can_debit_own_wallet() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        wallet_id, headers = await create_test_wallet(client, Decimal("20.00"))
        response = await client.post(
            f"/wallets/{wallet_id}/debit",
            headers=headers,
            json={
                "amount": "5.00",
                "idempotency_key": f"valid-{wallet_id}",
            },
        )

    assert response.status_code == 200, response.text
    assert response.json()["updated_balance"] == "15.00"
