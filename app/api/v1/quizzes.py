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
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Quiz, Question
from app.extensions import db, limiter
from collections import OrderedDict
from sqlalchemy import or_


@api_v1.route('/quiz', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def create_quiz():
    """Create new quiz"""
    try:
        user_id = get_jwt_identity()

        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Invalid JSON",
                "details": "Request content must be 'application/json'"
            }), 400

        try:
            data = request.get_json()
        except Exception as parse_error:
            return jsonify({
                "success": False,
                "error": "Failed to parse JSON",
                "details": str(parse_error)
            }), 400

        required_fields = ['title', 'duration']
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
                
        if 'description' in data:
            description=data.get('description').strip()
        else:
            description=None
        title=data.get('title').strip()
        category_id=data.get('category_id', '1')
        duration=data.get('duration')
        public=data.get('public', False)

        # Validating category_id
        if not category_id.isdigit():
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": "category_id must be a valid integer."
            }), 400
        category_id = int(category_id)

        # Validating duration
        if not isinstance(duration, int):
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": "duration must be an integer."
            }), 400

        # Validating public
        if not isinstance(public, bool):
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": "public must be a boolean value (true or false)."
            }), 400

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

        try:
            page = int(request.args.get('page', '1'))
            per_page = int(request.args.get('limit', '10'))
            if page <= 0 or per_page <= 0:
                raise ValueError("Pagination values must be positive integers.")
        except ValueError as ve:
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": str(ve)
            }), 400

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
                ("created_by", f'{quiz.User.first_name} {quiz.User.last_name}')
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
            "last" : url_for('api_v1.get_all_quiz', page=pages, limit=per_page, _external=True) if pages > 0 else None
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
    
    except ValueError as ve:
        logger.error(f"ValueError: {ve}")
        return jsonify({"success": False, "error": "Bad Request", "message": str(ve)}), 400

    except Exception as e:
        logger.error(f"Unexpected error in get_all_quiz: {e}")
        return jsonify({"success": False, "error": "Internal Server Error", "details": str(e)}), 500


@api_v1.route('/quiz/me', methods=['GET'])
@jwt_required()
@limiter.limit("20 per minute")
def get_user_quiz():
    """Retrieve paginated quizzes created by the logged-in user"""
    try:
        user_id = get_jwt_identity()

        try:
            page = int(request.args.get('page', '1'))
            per_page = int(request.args.get('limit', '10'))
            if page <= 0 or per_page <= 0:
                raise ValueError("Pagination values must be positive integers.")
        except ValueError as ve:
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": str(ve)
            }), 400

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
            "last" : url_for('api_v1.get_user_quiz', page=pages, limit=per_page, _external=True) if pages > 0 else None
        })

        response_data = OrderedDict({
            "success": True,
            "data": result,
            "total": total,
            "pages": pages,
            "links": links
        })

        return jsonify(response_data), 200 # Test hereeeeeeeeeeeeeeee
        response_json = json.dumps(response_data, default=str, sort_keys=False)
        return Response(response_json, status=200, mimetype='application/json')
     
    except ValueError as ve:
        logger.error(f"ValueError: {ve}")
        return jsonify({"success": False, "error": "Bad Request", "message": str(ve)}), 400

    except Exception as e:
        logger.error(f"Unexpected error in get_user_quiz: {e}")
        return jsonify({"success": False, "error": "Internal Server Error", "details": str(e)}), 500  
        #  return jsonify({
        #     "success": False,
        #     "error": "Internal Server Error",
        #     "details": "An unexpected error occurred."
        # }), 500

@api_v1.route('/quiz/<quiz_id>', methods=['GET'])
@jwt_required(optional=True)
@limiter.limit("20 per minute")
def get_quiz(quiz_id):
    """Retrieve a specific quiz, including its paginated questions"""
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

        try:
            page = int(request.args.get('page', '1'))
            per_page = int(request.args.get('limit', '10'))
            if page <= 0 or per_page <= 0:
                raise ValueError("Pagination values must be positive integers.")
        except ValueError as ve:
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": str(ve)
            }), 400

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
            "last" : url_for('api_v1.get_quiz', quiz_id=quiz_id, page=pages, limit=per_page, _external=True) if pages > 0 else None
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
    
    except ValueError as ve:
        logger.error(f"ValueError: {ve}")
        return jsonify({"success": False, "error": "Bad Request", "message": str(ve)}), 400

    except Exception as e:
        logger.error(f"Unexpected error in get_quiz: {e}")
        return jsonify({
            "success": False,
            "error": "Internal Server Error",
            "details": "An unexpected error occurred."
        }), 500


@api_v1.route('/quiz/<quiz_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("10 per minute")
def update_quiz(quiz_id):
    """Update the details of a specific quiz"""
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Invalid JSON",
                "details": "Request content must be 'application/json'"
            }), 400

        try:
            data = request.get_json()
        except Exception as parse_error:
            return jsonify({
                "success": False,
                "error": "Failed to parse JSON",
                "details": str(parse_error)
            }), 400
            
        if not data:
            return jsonify({"success": False, "error": "Invalid input", "message": "Request body is missing or malformed"}), 400

        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({"succes": False, "error": "Quiz not found"}), 404

        user_id = get_jwt_identity()
        if quiz.created_by != user_id:
            return jsonify({
                "success": False,
                "error": "Unauthorized to update this quiz"
            }), 403

        if 'title' in data:
            quiz.title = data['title']
        if 'description' in data:
            quiz.description = data['description']
        if 'duration' in data:
            try:
                quiz.duration = int(data['duration'])
                if quiz.duration <= 0:
                    raise ValueError("Duration must be a positive integer")
            except ValueError as ve:
                return jsonify({"success": False, "error": "Invalid input", "message": str(ve)}), 400
        if 'public' in data:
            if not isinstance(data['public'], bool):
                return jsonify({"success": False, "error": "Invalid input", "message": "Public must be a boolean"}), 400
            quiz.public = data['public']

        db.session.commit()
        return jsonify({"success": True, "message": "Quiz updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in update_quiz: {e}")
        return jsonify({"success": False, "error": "Failed to update quiz", "details": str(e)}), 400


@api_v1.route('/quiz/<quiz_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("10 per minute")
def delete_quiz(quiz_id):
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Invalid JSON",
                "details": "Request content must be 'application/json'"
            }), 400

        try:
            data = request.get_json()
        except Exception as parse_error:
            return jsonify({
                "success": False,
                "error": "Failed to parse JSON",
                "details": str(parse_error)
            }), 400
            
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
        logger.error(f"Unexpected error in delete_quiz: {e}")
        return jsonify({"success": False, "error": "Failed to delete quiz", "details": str(e)}), 400