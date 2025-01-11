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
from app.models import Quiz
from app.extensions import db, limiter
from collections import OrderedDict

@api_v1.route('/quiz', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def create_quiz():
    """Create new quiz"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        title=data.get('title', '')
        if not title:
            return jsonify({"success": False, "error": "Quiz Title is required"}), 400
        
        description=data.get('description')
        category_id=int(data.get('category_id', '1'))
        duration=data.get('duration', 30)
        public=data.get('public', False)

        new_quiz = Quiz(
            title=title,
            description=description,
            category_id=category_id,
            created_by=user_id,
            public=public
        )

        db.add(new_quiz)
        db.commit()
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

        print(Quiz.query.filter_by(created_by=user_id).all())
        print(Quiz.query.all())

        if user_id:
            query = Quiz.query.filter_by(public=True) if public_only else Quiz.query
            query = query.filter((Quiz.public == True) | (Quiz.created_by == user_id))
        else:
            query = Quiz.query.filter_by(public=True)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        print(pagination)
        quizzes = pagination.items
        total = pagination.total
        pages = pagination.pages
                    
        result = [
            {
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "duration": quiz.duration,
                "category": quiz.category_id,
                "public": quiz.public,
                "max_score": quiz.max_score,
                "created_at": quiz.created_at
            }
            for quiz in quizzes
        ]

        # HATEOAS links
        links = {
            "self" : url_for('api_v1.get_all_quiz', page=page, limit=per_page, _external=True),
            "next" : url_for('api_v1.get_all_quiz', page=page+1, limit=per_page, _external=True) if pagination.has_next else None,
            "prev" : url_for('api_v1.get_all_quiz', page=page-1, limit=per_page, _external=True) if pagination.has_prev else None,
            "first" : url_for('api_v1.get_all_quiz', page=1, limit=per_page, _external=True),
            "prev" : url_for('api_v1.get_all_quiz', page=pages, limit=per_page, _external=True)
        } 

        return jsonify({"success": True, "data": result, "total": total, "pages": pages, "links": links}), 200
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
                ("duration", quiz.duration),
                ("category", quiz.category_id),
                ("public", quiz.public),
                ("max_score", quiz.max_score),
                ("created_at", quiz.created_at),
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
def get_quiz():
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

        paginated_questions = Quiz.query.get(quiz_id).questions.paginate(page=page, per_page=per_page, error_out=False)
        questions = [
            {
                "id": question.id,
                "question_type": question.question_type,
                "question_text": question.question_text,
                "points": question.points,
                "is_multiple_response": question.is_multiple_response,
                "answer_choices": question.answer_choices
            }

            for question in paginated_questions.items
        ]

        return jsonify({
                "success": True,
                "data": {
                    "id": quiz.id,
                    "title": quiz.title,
                    "description": quiz.description,
                    "duration": quiz.duration,
                    "category": quiz.category_id,
                    "public": quiz.public,
                    "max_score": quiz.max_score,
                    "created_at": quiz.created_at,
                    "questions": questions,
                    "pagination": {
                        "page": paginated_questions.page,
                        "limit": paginated_questions.per_page,
                        "total_pages": paginated_questions.pages,
                        "total_items": paginated_questions.total
                    }
                }
            }), 200
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to retrieve quiz", "details": str(e)}), 500
    
@api_v1.route('/quiz/<quiz_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("10 per minute")
def update_quiz():
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
def delete_quiz():
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
        return jsonify({"success": True, "message": "Quiz deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to delete quiz", "details": str(e)}), 400