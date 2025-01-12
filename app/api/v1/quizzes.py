"""Quiz related endpoints
    Defined routes:
      - '/quiz' POST -> create_quiz
      - '/quiz' GET -> get_all_quiz
      - '/quiz/me' GET -> get_user_quiz
      - '/quiz/<quiz_id>' GET -> get_quiz
      - '/quiz/<quiz_id>' PUT -> update_quiz
      - '/quiz/<quiz_id>' DELETE -> delete_quiz
"""


from . import api_v1
from flask import request, jsonify, url_for, Response
import json
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity, verify_jwt_in_request, exceptions as jwt_exceptions
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from app.models import Quiz, Question
from app.extensions import db, limiter
from app.routes import logger
from collections import OrderedDict
from sqlalchemy import or_
from werkzeug.exceptions import Unauthorized


@api_v1.before_request
def check_token_revocation():
    print("testing")
    try:
        verify_jwt_in_request()  # Verify the JWT token in the request
        jwt_data = get_jwt()
        # You can add custom checks here for revoked tokens, like checking a blacklist or database.
        if jwt_data.get("revoked", False):  # Example custom check for revocation
            raise Unauthorized("Token has been revoked")
    except Unauthorized:
        response = {
            "success": False,
            "error": 401,
            "message": "Your token has been revoked. Please log in again."
        }
        return jsonify(response), 401
    except Exception as e:
        response = {
            "success": False,
            "error": 500,
            "message": str(e)
        }
        return jsonify(response), 500

@api_v1.errorhandler(429)
def handle_rate_limit_error(e):
    response = {
        "success": False,
        "error": 429,
        "message": "Too many requests. Please try again later"
    }
    return jsonify(response), 429


@api_v1.errorhandler(422)
def handle_missing_authorization_header(e):
    response = {
        "success": False,
        "error": "Missing Authorization Header",
        "message": "Request must include an Authorization header with a valid JWT token"
    }
    return jsonify(response), 422


@api_v1.errorhandler(Unauthorized)
def handle_revoked_token_error(e):
    response = {
        "success": False,
        "error": 401,
        "message": "Your token has been revoked. Please log in again."
    }
    return jsonify(response), 401


@api_v1.errorhandler(405)
def handle_not_allowed_error(e):
    logger.error(f"Method not allowed error: {str(e)}")
    response = {
        "success": False,
        "error": 405,
        "message": "Method Not Allowed"
    }
    return jsonify(response), 405

@api_v1.errorhandler(404)
def handle_not_found_error(e):
    response = {
        "success": False,
        "error": 404,
        "message": "Endpoint not found"
    }
    return jsonify(response), 404

@api_v1.errorhandler(ExpiredSignatureError)
def handle_expired_token_error(e):
    response = {
        "success": False,
        "error": 401,
        "message": "Your session has expired. Please log in again."
    }
    return jsonify(response), 401

@api_v1.errorhandler(InvalidTokenError)
def handle_invalid_token_error(e):
    response = {
        "success": False,
        "error": 400,
        "message": "Invalid token. Please provide a valid token."
    }
    return jsonify(response), 400


@api_v1.errorhandler(Exception)
def handle_generic_error(e):
    response = {
        "success": False,
        "error": "Internal Server Error",
        "message": "An unexpected error occurred. Please try again later."
    }
    logger.error(f"Unhandled exception: {e}")
    return jsonify(response), 500

@api_v1.route('/quiz', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def create_quiz():
    """Create new quiz"""
    try:
        user_id = get_jwt_identity()
        data = request.json

        required_fields = ['title', 'duration']
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
                
        title=data.get('title', '')
        description=data.get('description')
        category_id=int(data.get('category_id', '1'))
        duration=int(data.get('duration'))
        public=data.get('public', False)

        new_quiz = Quiz(
            title=title,
            description=description,
            category_id=category_id,
            created_by=user_id,
            duration = duration,
            public=public
        )

        db.session.add(new_quiz)
        db.session.commit()
        return jsonify({"success": True, "quiz": new_quiz.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to create quiz", "details": str(e)}), 400


@api_v1.route('/quiz', methods=['GET'])
@jwt_required(optional=True)
@limiter.limit("20 per minute")
def get_all_quiz():
    """Retrieve paginated quizzes created by the logged-in user and/or quizzes that are public"""
    try:
        user_id = get_jwt_identity()
        public_only = request.args.get('public', 'true').lower() =='true'
        page = int(request.args.get('page', '1'))
        per_page = int(request.args.get('limit', 10))

        if user_id:
            if public_only:
                query = Quiz.query.filter_by(public=True)
            else:
                query = Quiz.query.filter(
                    or_(Quiz.public==True, Quiz.created_by == user_id)
                )
        else:
            query = Quiz.query.filter_by(public=True)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        quizzes = pagination.items
        total = pagination.total
        pages = pagination.pages

        result = [
            OrderedDict([
                ("id", quiz.id),
                ("title", quiz.title),
                ("description", quiz.description),
                ("duration", f'{quiz.duration} minute(s)'),
                ("category", quiz.related_category.name if quiz.related_category else None),
                ("public", quiz.public),
                ("question_count", len(quiz.questions)),
                ("max_score", quiz.max_score),
                ("created_at", quiz.created_at.strftime('%Y-%m-%d')),
            ])
            for quiz in quizzes
        ]

        # HATEOAS links
        links = OrderedDict({
            "self" : url_for('api_v1.get_all_quiz', page=page, limit=per_page, _external=True),
            "next" : url_for('api_v1.get_all_quiz', page=page+1, limit=per_page, _external=True) if pagination.has_next else None,
            "prev" : url_for('api_v1.get_all_quiz', page=page-1, limit=per_page, _external=True) if pagination.has_prev else None,
            "first" : url_for('api_v1.get_all_quiz', page=1, limit=per_page, _external=True),
            "last" : url_for('api_v1.get_all_quiz', page=pages, limit=per_page, _external=True)
        })

        response_data = OrderedDict({
            "success": True,
            "data": result,
            "total": total,
            "pages": pages,
            "links": links
        })

        response_json = json.dumps(response_data, default=str, sort_keys=False)
        return Response(response_json, status=200, mimetype='application/json')

    except Exception as e:
        return jsonify({"success": False, "error": "Failed to fetch quizzes", "details": str(e)}), 500


@api_v1.route('/quiz/me', methods=['GET'])
@jwt_required()
@limiter.limit("20 per minute")
def get_user_quiz():
    """Retrieve paginated quizzes created by the logged-in user"""
    try:
        user_id = get_jwt_identity()
        
        page = int(request.args.get('page', '1'))
        per_page = int(request.args.get('limit', 10))

        query =  Quiz.query.filter_by(created_by=user_id)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        quizzes = pagination.items
        total = pagination.total
        pages = pagination.pages
                    
        result = [
            OrderedDict([
                ("id", quiz.id),
                ("title", quiz.title),
                ("description", quiz.description),
                ("duration", f'{quiz.duration} minute(s)'),
                ("category", quiz.related_category.name if quiz.related_category else None),
                ("public", quiz.public),
                ("question_count", len(quiz.questions)),
                ("max_score", quiz.max_score),
                ("created_at", quiz.created_at.strftime('%Y-%m-%d')),
            ])
            for quiz in quizzes
        ]

        # HATEOAS links
        links = OrderedDict({
            "self" : url_for('api_v1.get_user_quiz', page=page, limit=per_page, _external=True),
            "next" : url_for('api_v1.get_user_quiz', page=page+1, limit=per_page, _external=True) if pagination.has_next else None,
            "prev" : url_for('api_v1.get_user_quiz', page=page-1, limit=per_page, _external=True) if pagination.has_prev else None,
            "first" : url_for('api_v1.get_user_quiz', page=1, limit=per_page, _external=True),
            "last" : url_for('api_v1.get_user_quiz', page=pages, limit=per_page, _external=True)
        })

        response_data = OrderedDict({
            "success": True,
            "data": result,
            "total": total,
            "pages": pages,
            "links": links
        })

        response_json = json.dumps(response_data, default=str, sort_keys=False)
        return Response(response_json, status=200, mimetype='application/json')

    except Exception as e:
        return jsonify({"success": False, "error": "Failed to fetch user quizzes", "details": str(e)}), 500    

@api_v1.route('/quiz/<quiz_id>', methods=['GET'])
@jwt_required(optional=True)
@limiter.limit("20 per minute")
def get_quiz(quiz_id):
    try:
        user_id = get_jwt_identity()
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({
                "success": False,
                "error": "Quiz not found"
            }), 404
        
        if not quiz.public and (quiz.created_by != user_id):
            return jsonify({
                "success": False,
                "error": "Unauthorized access"
            }), 403

        page = int(request.args.get('page', '1'))
        per_page = int(request.args.get('limit', '10'))

        paginated_questions = (
            Question.query.filter_by(quiz_id=quiz_id)
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        total = paginated_questions.total
        pages = paginated_questions.pages
        
        questions = [
            OrderedDict([
                ("id", question.id),
                ("question_type", question.question_type),
                ("question_text", question.question_text),
                ("points", question.points),
                ("is_multiple_response", question.is_multiple_response),
                ("answer_choices", [
                    OrderedDict([
                        ("id", answer_choice.id),
                        ("text", answer_choice.text),
                        ("is_correct", answer_choice.is_correct)
                    ])      
                    for answer_choice in question.answer_choices
                ])
            ])
            for question in paginated_questions.items                
        ]

        result = [
            OrderedDict([
                 ("id", quiz.id),
                ("title", quiz.title),
                ("description", quiz.description),
                ("duration", f'{quiz.duration} minute(s)'),
                ("category", quiz.related_category.name if quiz.related_category else None),
                ("public", quiz.public),
                ("question_count", len(quiz.questions)),
                ("max_score", quiz.max_score),
                ("created_at", quiz.created_at.strftime('%Y-%m-%d')),
                ("questions", questions),
            ])
        ]
        
        # HATEOAS links
        links = OrderedDict({
            "self" : url_for('api_v1.get_quiz', quiz_id=quiz_id, page=page, limit=per_page, _external=True),
            "next" : url_for('api_v1.get_quiz', quiz_id=quiz_id, page=page+1, limit=per_page, _external=True) if paginated_questions.has_next else None,
            "prev" : url_for('api_v1.get_quiz', quiz_id=quiz_id, page=page-1, limit=per_page, _external=True) if paginated_questions.has_prev else None,
            "first" : url_for('api_v1.get_quiz', quiz_id=quiz_id, page=1, limit=per_page, _external=True),
            "last" : url_for('api_v1.get_quiz', quiz_id=quiz_id, page=pages, limit=per_page, _external=True)
        })

        response_data = OrderedDict({
            "success": True,
            "data": result,
            "total_items": total,
            "total_pages": pages,
            "links": links
        })
        response_json = json.dumps(response_data, default=str, sort_keys=False)
        return Response(response_json, status=200, mimetype='application/json')
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to retrieve quiz", "details": str(e)}), 500
    
@api_v1.route('/quiz/<quiz_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("10 per minute")
def update_quiz(quiz_id):
    try:
        data = request.json
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({"succes": False, "error": "Quiz not found"}), 404

        user_id = get_jwt_identity()
        if quiz.created_by != user_id:
            return jsonify({
                "success": False,
                "error": "Unauthorized to update this quiz"
            }), 403

        quiz.title = data.get('title', quiz.title)
        quiz.description = data.get('description', quiz.description)
        quiz.duration = int(data.get('duration', quiz.duration))
        quiz.public = data.get('public', quiz.public)
        
        db.session.commit()
        return jsonify({"success": True, "message": "Quiz updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to update quiz", "details": str(e)}), 400


@api_v1.route('/quiz/<quiz_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("10 per minute")
def delete_quiz(quiz_id):
    try:
        data = request.json
        user_id = get_jwt_identity()
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({"succes": False, "error": "Quiz not found"}), 404

        if quiz.created_by != user_id:
            return jsonify({
                "success": False,
                "error": "Unauthorized to delete this quiz"
            }), 403

        db.session.delete(quiz)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to delete quiz", "details": str(e)}), 400