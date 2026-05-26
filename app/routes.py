from flask import Blueprint, request, jsonify
from app.services import WalletService
from decimal import Decimal

wallet_bp = Blueprint('wallet', __name__)

# Error handler decorator
def handle_errors(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    wrapper.__name__ = f.__name__
    return wrapper

@wallet_bp.route('/create-user', methods=['POST'])
@handle_errors
def create_user():
    """Create a new user with wallet"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'email' not in data:
        return jsonify({'error': 'Missing username or email'}), 400
    
    user, wallet = WalletService.create_wallet(data['username'], data['email'])
    
    return jsonify({
        'message': 'User and wallet created successfully',
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'wallet_id': wallet.id,
        'balance': str(wallet.balance)
    }), 201

@wallet_bp.route('/credit', methods=['POST'])
@handle_errors
def credit():
    """Credit money to wallet"""
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'amount' not in data:
        return jsonify({'error': 'Missing user_id or amount'}), 400
    
    transaction = WalletService.credit_wallet(
        data['user_id'],
        Decimal(str(data['amount'])),
        data.get('description')
    )
    
    return jsonify({
        'message': 'Credit successful',
        'transaction_id': transaction.id,
        'amount': str(transaction.amount),
        'balance_after': str(transaction.balance_after),
        'timestamp': transaction.created_at.isoformat()
    }), 200

@wallet_bp.route('/debit', methods=['POST'])
@handle_errors
def debit():
    """Debit money from wallet"""
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'amount' not in data:
        return jsonify({'error': 'Missing user_id or amount'}), 400
    
    transaction = WalletService.debit_wallet(
        data['user_id'],
        Decimal(str(data['amount'])),
        data.get('description')
    )
    
    return jsonify({
        'message': 'Debit successful',
        'transaction_id': transaction.id,
        'amount': str(transaction.amount),
        'balance_after': str(transaction.balance_after),
        'timestamp': transaction.created_at.isoformat()
    }), 200

@wallet_bp.route('/balance/<int:user_id>', methods=['GET'])
@handle_errors
def get_balance(user_id):
    """Get wallet balance"""
    balance = WalletService.get_wallet_balance(user_id)
    
    return jsonify({
        'user_id': user_id,
        'balance': str(balance)
    }), 200

@wallet_bp.route('/history/<int:user_id>', methods=['GET'])
@handle_errors
def get_history(user_id):
    """Get transaction history"""
    limit = request.args.get('limit', default=None, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    transactions = WalletService.get_transaction_history(user_id, limit, offset)
    
    history = []
    for txn in transactions:
        history.append({
            'transaction_id': txn.id,
            'type': txn.transaction_type,
            'amount': str(txn.amount),
            'balance_before': str(txn.balance_before),
            'balance_after': str(txn.balance_after),
            'description': txn.description,
            'timestamp': txn.created_at.isoformat()
        })
    
    return jsonify({
        'user_id': user_id,
        'transaction_count': len(history),
        'transactions': history
    }), 200

@wallet_bp.route('/user/<int:user_id>', methods=['GET'])
@handle_errors
def get_user(user_id):
    """Get user info with wallet balance"""
    user = WalletService.get_user(user_id)
    
    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'balance': str(user.wallet.balance) if user.wallet else '0.00',
        'created_at': user.created_at.isoformat()
    }), 200
