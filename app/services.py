from decimal import Decimal
from app.models import db, User, Wallet, Ledger

class WalletService:
    """Service layer for wallet operations"""
    
    @staticmethod
    def create_wallet(username, email):
        """
        Create a wallet for a new user
        
        Args:
            username (str): Username for the user
            email (str): Email for the user
            
        Returns:
            tuple: (User, Wallet) objects if successful, (None, None) if user exists
        """
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            raise ValueError(f"User {username} already exists")
        
        try:
            # Create user
            user = User(username=username, email=email)
            db.session.add(user)
            db.session.flush()  # Flush to get the user ID
            
            # Create wallet for user
            wallet = Wallet(user_id=user.id, balance=Decimal('0.00'))
            db.session.add(wallet)
            db.session.commit()
            
            return user, wallet
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def credit_wallet(user_id, amount, description=None):
        """
        Add money to user's wallet
        
        Args:
            user_id (int): User ID
            amount (float/Decimal): Amount to credit
            description (str): Optional transaction description
            
        Returns:
            Ledger: Transaction record
        """
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        wallet = user.wallet
        if not wallet:
            raise ValueError(f"Wallet not found for user {user_id}")
        
        try:
            balance_before = wallet.balance
            wallet.balance += amount
            
            # Create ledger entry
            ledger_entry = Ledger(
                user_id=user_id,
                wallet_id=wallet.id,
                transaction_type='CREDIT',
                amount=amount,
                balance_before=balance_before,
                balance_after=wallet.balance,
                description=description or 'Credit transaction'
            )
            
            db.session.add(ledger_entry)
            db.session.commit()
            
            return ledger_entry
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def debit_wallet(user_id, amount, description=None):
        """
        Remove money from user's wallet
        
        Args:
            user_id (int): User ID
            amount (float/Decimal): Amount to debit
            description (str): Optional transaction description
            
        Returns:
            Ledger: Transaction record
            
        Raises:
            ValueError: If amount is invalid or insufficient balance
        """
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValueError("Debit amount must be positive")
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        wallet = user.wallet
        if not wallet:
            raise ValueError(f"Wallet not found for user {user_id}")
        
        if wallet.balance < amount:
            raise ValueError(f"Insufficient balance. Current balance: {wallet.balance}, Requested: {amount}")
        
        try:
            balance_before = wallet.balance
            wallet.balance -= amount
            
            # Create ledger entry
            ledger_entry = Ledger(
                user_id=user_id,
                wallet_id=wallet.id,
                transaction_type='DEBIT',
                amount=amount,
                balance_before=balance_before,
                balance_after=wallet.balance,
                description=description or 'Debit transaction'
            )
            
            db.session.add(ledger_entry)
            db.session.commit()
            
            return ledger_entry
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_wallet_balance(user_id):
        """
        Get current wallet balance for user
        
        Args:
            user_id (int): User ID
            
        Returns:
            Decimal: Current balance
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        wallet = user.wallet
        if not wallet:
            raise ValueError(f"Wallet not found for user {user_id}")
        
        return wallet.balance
    
    @staticmethod
    def get_transaction_history(user_id, limit=None, offset=0):
        """
        Get transaction history (ledger) for user
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of transactions to return
            offset (int): Offset for pagination
            
        Returns:
            list: List of Ledger entries
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        query = Ledger.query.filter_by(user_id=user_id).order_by(Ledger.created_at.desc())
        
        if limit:
            query = query.limit(limit).offset(offset)
        
        return query.all()
    
    @staticmethod
    def get_user(user_id):
        """
        Get user by ID
        
        Args:
            user_id (int): User ID
            
        Returns:
            User: User object
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user
