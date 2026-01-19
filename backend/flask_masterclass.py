from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_models import Course
from flask_app import db

masterclass_bp = Blueprint('masterclass', __name__)


@masterclass_bp.route('/courses', methods=['GET'])
@jwt_required()
def get_courses():
    """Get all courses"""
    try:
        level = request.args.get('level')
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        query = Course.query
        
        if level:
            query = query.filter_by(level=level)
        
        if category:
            query = query.filter_by(category=category)
        
        courses = query.order_by(Course.created_date.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return jsonify([c.to_dict() for c in courses]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@masterclass_bp.route('/courses/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    """Get specific course details"""
    try:
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        return jsonify(course.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@masterclass_bp.route('/courses', methods=['POST'])
@jwt_required()
def create_course():
    """Create a new course (admin only)"""
    try:
        data = request.get_json()
        
        course = Course(
            title=data.get('title'),
            description=data.get('description'),
            level=data.get('level'),
            category=data.get('category'),
            duration_minutes=data.get('duration_minutes'),
            video_url=data.get('video_url'),
            thumbnail_url=data.get('thumbnail_url'),
            is_premium=data.get('is_premium', False)
        )
        
        db.session.add(course)
        db.session.commit()
        
        return jsonify({
            'message': 'Course created successfully',
            'course': course.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@masterclass_bp.route('/courses/<int:course_id>', methods=['PUT'])
@jwt_required()
def update_course(course_id):
    """Update course (admin only)"""
    try:
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        for field in ['title', 'description', 'level', 'category', 'duration_minutes', 
                      'video_url', 'thumbnail_url', 'is_premium']:
            if field in data:
                setattr(course, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Course updated successfully',
            'course': course.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@masterclass_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@jwt_required()
def delete_course(course_id):
    """Delete course (admin only)"""
    try:
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        db.session.delete(course)
        db.session.commit()
        
        return jsonify({'message': 'Course deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@masterclass_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get learning statistics"""
    try:
        stats = {
            'total_courses': Course.query.count(),
            'beginner_courses': Course.query.filter_by(level='beginner').count(),
            'intermediate_courses': Course.query.filter_by(level='intermediate').count(),
            'advanced_courses': Course.query.filter_by(level='advanced').count(),
            'premium_courses': Course.query.filter_by(is_premium=True).count()
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500