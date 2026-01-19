from flask_app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    challenges = db.relationship('Challenge', backref='user', lazy=True, cascade='all, delete-orphan')
    trades = db.relationship('Trade', backref='user', lazy=True, cascade='all, delete-orphan')
    posts = db.relationship('CommunityPost', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'created_date': self.created_date.isoformat()
        }


class Challenge(db.Model):
    __tablename__ = 'challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tier = db.Column(db.String(20), nullable=False)  # 'starter', 'pro', 'elite'
    initial_balance = db.Column(db.Float, nullable=False)
    current_balance = db.Column(db.Float, nullable=False)
    highest_balance = db.Column(db.Float, nullable=False)
    daily_start_balance = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'passed', 'failed'
    fail_reason = db.Column(db.String(255))
    profit_percent = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(20))  # 'cmi', 'crypto', 'paypal'
    amount_paid = db.Column(db.Float)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trades = db.relationship('Trade', backref='challenge', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user.email,
            'tier': self.tier,
            'initial_balance': self.initial_balance,
            'current_balance': self.current_balance,
            'highest_balance': self.highest_balance,
            'daily_start_balance': self.daily_start_balance,
            'status': self.status,
            'fail_reason': self.fail_reason,
            'profit_percent': self.profit_percent,
            'payment_method': self.payment_method,
            'amount_paid': self.amount_paid,
            'created_date': self.created_date.isoformat(),
            'updated_date': self.updated_date.isoformat()
        }


class Trade(db.Model):
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    quantity = db.Column(db.Float, nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float)
    profit_loss = db.Column(db.Float)
    status = db.Column(db.String(20), default='open')  # 'open' or 'closed'
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'challenge_id': self.challenge_id,
            'user_email': self.user.email,
            'symbol': self.symbol,
            'type': self.type,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'profit_loss': self.profit_loss,
            'status': self.status,
            'created_date': self.created_date.isoformat(),
            'updated_date': self.updated_date.isoformat()
        }


class NewsArticle(db.Model):
    __tablename__ = 'news_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(100))
    category = db.Column(db.String(50))  # 'market', 'crypto', 'morocco', 'global'
    image_url = db.Column(db.String(500))
    external_url = db.Column(db.String(500))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'source': self.source,
            'category': self.category,
            'image_url': self.image_url,
            'external_url': self.external_url,
            'created_date': self.created_date.isoformat()
        }


class CommunityPost(db.Model):
    __tablename__ = 'community_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # 'strategy', 'analysis', 'question', 'general'
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'author_email': self.author.email,
            'author_name': self.author.full_name,
            'content': self.content,
            'category': self.category,
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'created_date': self.created_date.isoformat(),
            'updated_date': self.updated_date.isoformat()
        }


class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(50), nullable=False)  # 'beginner', 'intermediate', 'advanced'
    category = db.Column(db.String(50))  # 'technical', 'fundamental', 'risk_management', 'psychology'
    duration_minutes = db.Column(db.Integer)
    video_url = db.Column(db.String(500))
    thumbnail_url = db.Column(db.String(500))
    is_premium = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'level': self.level,
            'category': self.category,
            'duration_minutes': self.duration_minutes,
            'video_url': self.video_url,
            'thumbnail_url': self.thumbnail_url,
            'is_premium': self.is_premium,
            'created_date': self.created_date.isoformat()
        }