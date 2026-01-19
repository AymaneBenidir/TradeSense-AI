from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_models import User, Challenge, Trade
from flask_app import db
from datetime import datetime

trading_bp = Blueprint('trading', __name__)

# Tier configurations
TIER_CONFIG = {
    'starter': {
        'initial_balance': 10000,
        'price': 99,
        'max_daily_loss_percent': 5,
        'max_total_loss_percent': 10,
        'profit_target_percent': 10
    },
    'pro': {
        'initial_balance': 50000,
        'price': 299,
        'max_daily_loss_percent': 5,
        'max_total_loss_percent': 10,
        'profit_target_percent': 10
    },
    'elite': {
        'initial_balance': 100000,
        'price': 599,
        'max_daily_loss_percent': 5,
        'max_total_loss_percent': 10,
        'profit_target_percent': 10
    }
}


@trading_bp.route('/challenges', methods=['POST'])
@jwt_required()
def create_challenge():
    """Create a new trading challenge"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        data = request.get_json()
        tier = data.get('tier', '').lower()
        payment_method = data.get('payment_method')
        
        if tier not in TIER_CONFIG:
            return jsonify({'error': 'Invalid tier. Must be starter, pro, or elite'}), 400
        
        # Get tier configuration
        config = TIER_CONFIG[tier]
        initial_balance = config['initial_balance']
        
        # Create challenge
        challenge = Challenge(
            user_id=user.id,
            tier=tier,
            initial_balance=initial_balance,
            current_balance=initial_balance,
            highest_balance=initial_balance,
            daily_start_balance=initial_balance,
            payment_method=payment_method,
            amount_paid=config['price']
        )
        
        db.session.add(challenge)
        db.session.commit()
        
        return jsonify({
            'message': 'Challenge created successfully',
            'challenge': challenge.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@trading_bp.route('/challenges', methods=['GET'])
@jwt_required()
def get_challenges():
    """Get user's challenges"""
    try:
        user_id = get_jwt_identity()
        status = request.args.get('status')
        
        query = Challenge.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        challenges = query.order_by(Challenge.created_date.desc()).all()
        
        return jsonify([c.to_dict() for c in challenges]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trading_bp.route('/challenges/<int:challenge_id>', methods=['GET'])
@jwt_required()
def get_challenge(challenge_id):
    """Get specific challenge details"""
    try:
        user_id = get_jwt_identity()
        challenge = Challenge.query.filter_by(id=challenge_id, user_id=user_id).first()
        
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404
        
        return jsonify(challenge.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trading_bp.route('/trades', methods=['POST'])
@jwt_required()
def execute_trade():
    """Execute a trade"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        challenge_id = data.get('challenge_id')
        symbol = data.get('symbol', '').upper()
        trade_type = data.get('type', '').lower()
        quantity = float(data.get('quantity', 0))
        entry_price = float(data.get('entry_price', 0))
        
        # Validate inputs
        if trade_type not in ['buy', 'sell']:
            return jsonify({'error': 'Trade type must be buy or sell'}), 400
        
        if quantity <= 0 or entry_price <= 0:
            return jsonify({'error': 'Invalid quantity or price'}), 400
        
        # Get challenge
        challenge = Challenge.query.filter_by(id=challenge_id, user_id=user_id).first()
        
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404
        
        if challenge.status != 'active':
            return jsonify({'error': 'Challenge is not active'}), 400
        
        # Calculate trade value
        trade_value = quantity * entry_price
        
        # Check if user has enough balance
        if trade_value > challenge.current_balance:
            return jsonify({'error': 'Insufficient balance'}), 400
        
        # Create trade
        trade = Trade(
            challenge_id=challenge.id,
            user_id=user_id,
            symbol=symbol,
            type=trade_type,
            quantity=quantity,
            entry_price=entry_price
        )
        
        db.session.add(trade)
        db.session.commit()
        
        return jsonify({
            'message': 'Trade executed successfully',
            'trade': trade.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@trading_bp.route('/trades/<int:trade_id>/close', methods=['POST'])
@jwt_required()
def close_trade(trade_id):
    """Close an open trade"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        exit_price = float(data.get('exit_price', 0))
        
        if exit_price <= 0:
            return jsonify({'error': 'Invalid exit price'}), 400
        
        # Get trade
        trade = Trade.query.filter_by(id=trade_id, user_id=user_id).first()
        
        if not trade:
            return jsonify({'error': 'Trade not found'}), 404
        
        if trade.status != 'open':
            return jsonify({'error': 'Trade is already closed'}), 400
        
        # Calculate profit/loss
        if trade.type == 'buy':
            profit_loss = (exit_price - trade.entry_price) * trade.quantity
        else:  # sell
            profit_loss = (trade.entry_price - exit_price) * trade.quantity
        
        # Update trade
        trade.exit_price = exit_price
        trade.profit_loss = profit_loss
        trade.status = 'closed'
        
        # Update challenge balance
        challenge = trade.challenge
        challenge.current_balance += profit_loss
        challenge.highest_balance = max(challenge.highest_balance, challenge.current_balance)
        
        # Calculate profit percentage
        challenge.profit_percent = ((challenge.current_balance - challenge.initial_balance) / challenge.initial_balance) * 100
        
        # Check challenge rules
        config = TIER_CONFIG[challenge.tier]
        
        # Check daily loss limit (5%)
        daily_loss = challenge.daily_start_balance - challenge.current_balance
        max_daily_loss = challenge.daily_start_balance * (config['max_daily_loss_percent'] / 100)
        
        if daily_loss >= max_daily_loss:
            challenge.status = 'failed'
            challenge.fail_reason = f'Exceeded {config["max_daily_loss_percent"]}% daily loss limit'
        
        # Check total loss limit (10%)
        total_loss = challenge.initial_balance - challenge.current_balance
        max_total_loss = challenge.initial_balance * (config['max_total_loss_percent'] / 100)
        
        if total_loss >= max_total_loss:
            challenge.status = 'failed'
            challenge.fail_reason = f'Exceeded {config["max_total_loss_percent"]}% total loss limit'
        
        # Check profit target (10%)
        if challenge.profit_percent >= config['profit_target_percent']:
            challenge.status = 'passed'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Trade closed successfully',
            'trade': trade.to_dict(),
            'challenge': challenge.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@trading_bp.route('/trades', methods=['GET'])
@jwt_required()
def get_trades():
    """Get user's trades"""
    try:
        user_id = get_jwt_identity()
        challenge_id = request.args.get('challenge_id')
        status = request.args.get('status')
        
        query = Trade.query.filter_by(user_id=user_id)
        
        if challenge_id:
            query = query.filter_by(challenge_id=challenge_id)
        
        if status:
            query = query.filter_by(status=status)
        
        trades = query.order_by(Trade.created_date.desc()).all()
        
        return jsonify([t.to_dict() for t in trades]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trading_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get trading leaderboard"""
    try:
        # Get top performers
        challenges = Challenge.query.filter_by(status='active')\
            .order_by(Challenge.profit_percent.desc())\
            .limit(100)\
            .all()
        
        leaderboard = []
        for idx, challenge in enumerate(challenges, 1):
            leaderboard.append({
                'rank': idx,
                'trader': challenge.user.full_name or 'Anonymous',
                'profit_percent': round(challenge.profit_percent, 2),
                'balance': challenge.current_balance,
                'tier': challenge.tier
            })
        
        return jsonify(leaderboard), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500