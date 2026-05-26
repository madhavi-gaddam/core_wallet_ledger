import asyncio
import uuid
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.database import SessionLocal
from app.main import app
from app.models.ledger_entry import LedgerEntry, TransactionType
from app.models.wallet import Wallet


async def create_test_wallet(client: AsyncClient, balance: Decimal) -> int:
    user_response = await client.post(
        "/users",
        json={
            "username": f"test_{uuid.uuid4().hex[:12]}",
            "email": f"test-{uuid.uuid4()}@example.com",
        },
    )
    assert user_response.status_code == 201, user_response.text

    wallet_response = await client.post(
        "/wallets",
        json={"user_id": user_response.json()["id"]},
    )
    assert wallet_response.status_code == 201, wallet_response.text
    wallet_id = int(wallet_response.json()["id"])

    with SessionLocal() as db:
        with db.begin():
            wallet = db.get(Wallet, wallet_id)
            assert wallet is not None
            wallet.balance = balance

    return wallet_id


@pytest.mark.asyncio
async def test_50_concurrent_debits_only_10_succeed() -> None:
    """Integration test for PostgreSQL row locks and atomic ledger writes."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        wallet_id = await create_test_wallet(client, Decimal("100.00"))

        async def debit_once(index: int):
            return await client.post(
                f"/wallets/{wallet_id}/debit",
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
        wallet_id = await create_test_wallet(client, Decimal("100.00"))
        payload = {
            "amount": "10.00",
            "idempotency_key": f"retry-{wallet_id}",
            "description": "retry debit",
        }

        first = await client.post(f"/wallets/{wallet_id}/debit", json=payload)
        second = await client.post(f"/wallets/{wallet_id}/debit", json=payload)

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
        wallet_id = await create_test_wallet(client, Decimal("5.00"))
        response = await client.post(
            f"/wallets/{wallet_id}/debit",
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
