
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_models import NewsArticle
from flask_app import db
from datetime import datetime, timedelta

news_bp = Blueprint('news', __name__)


@news_bp.route('/articles', methods=['GET'])
def get_articles():
    """Get news articles"""
    try:
        category = request.args.get('category')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        query = NewsArticle.query
        
        if category:
            query = query.filter_by(category=category)
        
        articles = query.order_by(NewsArticle.created_date.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return jsonify([a.to_dict() for a in articles]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@news_bp.route('/articles/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """Get specific article"""
    try:
        article = NewsArticle.query.get(article_id)
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        return jsonify(article.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@news_bp.route('/articles', methods=['POST'])
@jwt_required()
def create_article():
    """Create news article (admin only)"""
    try:
        data = request.get_json()
        
        article = NewsArticle(
            title=data.get('title'),
            summary=data.get('summary'),
            source=data.get('source'),
            category=data.get('category'),
            image_url=data.get('image_url'),
            external_url=data.get('external_url')
        )
        
        db.session.add(article)
        db.session.commit()
        
        return jsonify({
            'message': 'Article created successfully',
            'article': article.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@news_bp.route('/articles/<int:article_id>', methods=['DELETE'])
@jwt_required()
def delete_article(article_id):
    """Delete news article (admin only)"""
    try:
        article = NewsArticle.query.get(article_id)
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        db.session.delete(article)
        db.session.commit()
        
        return jsonify({'message': 'Article deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@news_bp.route('/trending', methods=['GET'])
def get_trending():
    """Get trending news from last 24 hours"""
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        articles = NewsArticle.query\
            .filter(NewsArticle.created_date >= yesterday)\
            .order_by(NewsArticle.created_date.desc())\
            .limit(10)\
            .all()
        
        return jsonify([a.to_dict() for a in articles]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500