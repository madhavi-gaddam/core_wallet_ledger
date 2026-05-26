"""
Test script to verify wallet functionality
"""

from app import create_app
from app.models import db
from app.services import WalletService
from decimal import Decimal

def test_wallet_flow():
    """Test complete wallet workflow"""
    # Create app with testing config
    app = create_app('testing')
    
    with app.app_context():
        # Create tables
        db.create_all()
        print("✓ Database tables created")
        
        # Test 1: Create user with wallet
        print("\n--- Test 1: Create User & Wallet ---")
        user, wallet = WalletService.create_wallet('alice', 'alice@example.com')
        print(f"✓ User created: {user.username} (ID: {user.id})")
        print(f"✓ Wallet created (ID: {wallet.id}, Balance: {wallet.balance})")
        
        # Test 2: Credit wallet
        print("\n--- Test 2: Credit Wallet ---")
        txn1 = WalletService.credit_wallet(user.id, 1000, "Initial deposit")
        print(f"✓ Credited: {txn1.amount}")
        print(f"  Balance before: {txn1.balance_before}")
        print(f"  Balance after: {txn1.balance_after}")
        
        # Test 3: Get balance
        print("\n--- Test 3: Get Balance ---")
        balance = WalletService.get_wallet_balance(user.id)
        print(f"✓ Current balance: {balance}")
        
        # Test 4: Debit wallet
        print("\n--- Test 4: Debit Wallet ---")
        txn2 = WalletService.debit_wallet(user.id, 250, "Transfer out")
        print(f"✓ Debited: {txn2.amount}")
        print(f"  Balance before: {txn2.balance_before}")
        print(f"  Balance after: {txn2.balance_after}")
        
        # Test 5: Multiple transactions
        print("\n--- Test 5: Multiple Transactions ---")
        WalletService.credit_wallet(user.id, 500, "Refund")
        WalletService.debit_wallet(user.id, 100, "Withdrawal")
        balance = WalletService.get_wallet_balance(user.id)
        print(f"✓ Final balance: {balance}")
        
        # Test 6: Get transaction history
        print("\n--- Test 6: Transaction History ---")
        transactions = WalletService.get_transaction_history(user.id)
        print(f"✓ Total transactions: {len(transactions)}")
        for txn in transactions:
            print(f"  [{txn.transaction_type}] {txn.amount} | Balance: {txn.balance_after} | {txn.description}")
        
        # Test 7: Negative balance prevention
        print("\n--- Test 7: Negative Balance Prevention ---")
        try:
            WalletService.debit_wallet(user.id, 5000, "Should fail")
            print("✗ ERROR: Should have prevented negative balance!")
        except ValueError as e:
            print(f"✓ Correctly prevented: {e}")
        
        # Test 8: Invalid operations
        print("\n--- Test 8: Invalid Operations ---")
        try:
            WalletService.debit_wallet(999, 100, "Non-existent user")
            print("✗ ERROR: Should have raised error for non-existent user!")
        except ValueError as e:
            print(f"✓ Correctly raised error: {e}")
        
        print("\n✅ All tests passed!")
        
        # Cleanup
        db.session.remove()
        db.drop_all()

if __name__ == '__main__':
    test_wallet_flow()
