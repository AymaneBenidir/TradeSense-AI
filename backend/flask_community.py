from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_models import User, CommunityPost
from flask_app import db

community_bp = Blueprint('community', __name__)


@community_bp.route('/posts', methods=['GET'])
@jwt_required()
def get_posts():
    """Get community posts"""
    try:
        category = request.args.get('category')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        query = CommunityPost.query
        
        if category:
            query = query.filter_by(category=category)
        
        posts = query.order_by(CommunityPost.created_date.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return jsonify([p.to_dict() for p in posts]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@community_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    """Create a new community post"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        data = request.get_json()
        content = data.get('content', '').strip()
        category = data.get('category', 'general')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        post = CommunityPost(
            author_id=user.id,
            content=content,
            category=category
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post created successfully',
            'post': post.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@community_bp.route('/posts/<int:post_id>', methods=['GET'])
@jwt_required()
def get_post(post_id):
    """Get specific post"""
    try:
        post = CommunityPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        return jsonify(post.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@community_bp.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    """Update post (author only)"""
    try:
        user_id = get_jwt_identity()
        post = CommunityPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        if post.author_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if 'content' in data:
            post.content = data['content'].strip()
        
        if 'category' in data:
            post.category = data['category']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Post updated successfully',
            'post': post.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@community_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    """Delete post (author or admin only)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        post = CommunityPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Only author or admin can delete
        if post.author_id != user_id and user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@community_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    """Like a post"""
    try:
        post = CommunityPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        post.likes_count += 1
        db.session.commit()
        
        return jsonify({
            'message': 'Post liked',
            'likes_count': post.likes_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500