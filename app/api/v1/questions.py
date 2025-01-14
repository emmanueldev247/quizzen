"""Quiz related endpoints
    Defined routes:
      - '.../question' POST -> create_question
      - '.../question/<question_id>' GET -> get_question
      - '.../question/<question_id>' PUT -> update_question
      - '.../question/<question_id>' DELETE -> delete_question
"""


import json
from collections import OrderedDict
from flask import request, jsonify, url_for, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

from app.extensions import api_v1, db, limiter
from app.models import AnswerChoice, Question, Quiz
from app.routes import logger
from app.routes_dashboard import update_answer_choices


question_route = '/quiz/<quiz_id>/question/<question_id>'

@api_v1.route('/quiz/<quiz_id>/question', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def create_question(quiz_id):
    """Create new question"""
    try:
        user_id = get_jwt_identity()
        quiz = Quiz.query.get(quiz_id)

        if not quiz:
            return jsonify({
                "success": False,
                "error": "Quiz not found"
            }), 404

        if quiz.created_by != user_id:
            return jsonify({
                "success": False,
                "error": "Unauthorized access"
            }), 403

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

        required_fields =\
            ['question_text', 'is_multiple_response', 'question_type', 'points', 'answer_choices']
        missing_fields =\
            [field for field in required_fields if not data.get(field)]

        if missing_fields:
            x_fields = ', '.join(missing_fields)
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": f"Missing required fields: {x_fields}"
            }), 400

        question_text = data['question_text'].strip()
        is_multiple_response = data['is_multiple_response']
        question_type = data['question_type'].strip()
        points = data['points']
        answer_choices = data['answer_choices']

        # Validating data
        if not isinstance(is_multiple_response, bool):
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": "is_multiple_response must be a boolean value (true or false)."
            }), 400
        is_multiple_response = bool(is_multiple_response)

        if question_type not in ['multiple_choice', 'short_answer']:
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": "question_type must be either 'multiple_choice' or 'short_answer'"
            }), 400

        if question_type == 'multiple_choice' and len(answer_choices) < 2:
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": "multiple_choice require more than 1 option"
            }), 400

        has_correct = False
        correct_count = 0
        for option in answer_choice:
            if not isinstance(option['is_correct'], bool):
                return jsonify({
                    "success": False,
                    "error": "Bad Request",
                    "message": "is_correct must be a boolean value (true or false)."
                }), 400
            option['is_correct'] = bool(option['is_correct'])
            if option['is_correct']:
                has_correct = True
                correct_count += 1

        if not has_correct:
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": "Please include a correct option"
            }), 400

        if not is_multiple_response and correct_count > 1:
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": "Please confirm that question has multiple correct answers"
            }), 400

        if is_multiple_response and correct_count < 2:
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": "Please confirm that question has only 1 correct answer"
            }), 400

        try:
            points = int(data['points'])
            if points <= 0:
                raise ValueError("Points must be a positive integer")
        except ValueError as ve:
            return jsonify({
                "success": False,
                "error": "Invalid input",
                "message": "Points must be a positive integer"
            }), 400
        
        try:
            page = int(request.args.get('page', '1'))
            per_page = int(request.args.get('limit', '10'))
            if page <= 0 or per_page <= 0:
                raise ValueError("Pagination values must be positive integers")
        except ValueError as ve:
            return jsonify({
                "success": False,
                "error": "Bad Request",
                "message": "Pagination values must be positive integers."
            }), 400

        new_question = Question(
            quiz_id=quiz_id,
            question_text=question_text,
            is_multiple_response=is_multiple_response,
            question_type=question_type,
            points=points,
        )
        db.session.add(new_question)

        update_answer_choices(new_question.id, answer_choices)
        quiz.calculate_max_score()
        db.session.commit()

        return jsonify({
            "success": True,
            "quiz": quiz_id,
            "question": new_question.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "Failed to create question"
        }), 400

# HEREEEEEEEEEEEEEEE
# @api_v1.route('/quiz', methods=['GET'])
# @jwt_required(optional=True)
# @limiter.limit("20 per minute")
# def get_all_quiz():
#     """Retrieve paginated quizzes created by the logged-in user
#         and/or quizzes that are public
#     """
#     try:
#         user_id = get_jwt_identity()
#         public_only = request.args.get('public', 'true').lower() == 'true'

#         try:
#             page = int(request.args.get('page', '1'))
#             per_page = int(request.args.get('limit', '10'))
#             if page <= 0 or per_page <= 0:
#                 raise ValueError("Pagination values must be positive integers")
#         except ValueError as ve:
#             return jsonify({
#                 "success": False,
#                 "error": "Bad Request",
#                 "message": "Pagination values must be positive integers."
#             }), 400

#         if user_id:
#             if public_only:
#                 query = Quiz.query.filter_by(public=True)
#             else:
#                 query = Quiz.query.filter(
#                     or_(Quiz.public, Quiz.created_by == user_id)
#                 )
#         else:
#             query = Quiz.query.filter_by(public=True)

#         pagination = query.paginate(
#             page=page, per_page=per_page, error_out=False
#         )
#         quizzes = pagination.items
#         total = pagination.total
#         pages = pagination.pages

#         result = [
#             OrderedDict([
#                 ("id", quiz.id),
#                 ("title", quiz.title),
#                 ("description", quiz.description),
#                 ("duration", f'{quiz.duration} minute(s)'),
#                 ("category", quiz.related_category.name
#                     if quiz.related_category else None),
#                 ("public", quiz.public),
#                 ("question_count", len(quiz.questions)),
#                 ("max_score", quiz.max_score),
#                 ("created_by", f'{quiz.user.first_name} {quiz.user.last_name}'
#                     if quiz.user else "Unknown User"),
#                 ("created_at", quiz.created_at.strftime('%Y-%m-%d')),
#             ])
#             for quiz in quizzes
#         ]

#         # HATEOAS links
#         links = OrderedDict({
#             "self": url_for('api_v1.get_all_quiz', page=page,
#                             limit=per_page, _external=True),
#             "next": url_for('api_v1.get_all_quiz', page=page+1, limit=per_page,
#                             _external=True) if pagination.has_next else None,
#             "prev": url_for('api_v1.get_all_quiz', page=page-1, limit=per_page,
#                             _external=True) if pagination.has_prev else None,
#             "first": url_for('api_v1.get_all_quiz', page=1,
#                              limit=per_page, _external=True),
#             "last": url_for('api_v1.get_all_quiz', page=pages, limit=per_page,
#                             _external=True) if pages > 0 else None
#         })

#         response_data = OrderedDict({
#             "success": True,
#             "data": result,
#             "total": total,
#             "pages": pages,
#             "links": links
#         })

#         response_json = json.dumps(response_data, default=str, sort_keys=False)
#         return Response(response_json, status=200, mimetype='application/json')

#     except ValueError as ve:
#         logger.error(f"ValueError: {ve}")
#         return jsonify({
#             "success": False,
#             "error": "Bad Request",
#             "message": "Pagination values must be positive integers"
#         }), 400

#     except Exception as e:
#         logger.error(f"Unexpected error in get_all_quiz: {e}")
#         return jsonify({
#             "success": False,
#             "error": "Internal Server Error"
#         }), 500


# @api_v1.route('/quiz/me', methods=['GET'])
# @jwt_required()
# @limiter.limit("20 per minute")
# def get_user_quiz():
#     """Retrieve paginated quizzes created by the logged-in user"""
#     try:
#         user_id = get_jwt_identity()

#         try:
#             page = int(request.args.get('page', '1'))
#             per_page = int(request.args.get('limit', '10'))
#             if page <= 0 or per_page <= 0:
#                 raise ValueError("Pagination values must be positive integers")
#         except ValueError as ve:
#             return jsonify({
#                 "success": False,
#                 "error": "Bad Request",
#                 "message": "Pagination values must be positive integers."
#             }), 400

#         query = Quiz.query.filter_by(created_by=user_id)
#         pagination = query.paginate(
#             page=page, per_page=per_page, error_out=False
#         )
#         quizzes = pagination.items
#         total = pagination.total
#         pages = pagination.pages

#         result = [
#             OrderedDict([
#                 ("id", quiz.id),
#                 ("title", quiz.title),
#                 ("description", quiz.description),
#                 ("duration", f'{quiz.duration} minute(s)'),
#                 ("category", quiz.related_category.name
#                     if quiz.related_category else None),
#                 ("public", quiz.public),
#                 ("question_count", len(quiz.questions)),
#                 ("max_score", quiz.max_score),
#                 ("created_at", quiz.created_at.strftime('%Y-%m-%d')),
#             ])
#             for quiz in quizzes
#         ]

#         # HATEOAS links
#         links = OrderedDict({
#             "self": url_for('api_v1.get_user_quiz', page=page,
#                             limit=per_page, _external=True),
#             "next": url_for('api_v1.get_user_quiz',
#                             page=page+1, limit=per_page,
#                             _external=True) if pagination.has_next else None,
#             "prev": url_for('api_v1.get_user_quiz',
#                             page=page-1, limit=per_page,
#                             _external=True) if pagination.has_prev else None,
#             "first": url_for('api_v1.get_user_quiz', page=1,
#                              limit=per_page, _external=True),
#             "last": url_for('api_v1.get_user_quiz', page=pages, limit=per_page,
#                             _external=True) if pages > 0 else None
#         })

#         response_data = OrderedDict({
#             "success": True,
#             "data": result,
#             "total": total,
#             "pages": pages,
#             "links": links
#         })

#         response_json = json.dumps(response_data, default=str, sort_keys=False)
#         return Response(response_json, status=200, mimetype='application/json')

#     except ValueError as ve:
#         logger.error(f"ValueError: {ve}")
#         return jsonify({
#             "success": False,
#             "error": "Bad Request",
#             "message": "Pagination values must be positive integers"
#         }), 400

#     except Exception as e:
#         logger.error(f"Unexpected error in get_user_quiz: {e}")
#         return jsonify({
#             "success": False,
#             "error": "Internal Server Error",
#             "details": "An unexpected error occurred."
#         }), 500


# @api_v1.route('/quiz/<quiz_id>', methods=['GET'])
# @jwt_required(optional=True)
# @limiter.limit("20 per minute")
# def get_quiz(quiz_id):
#     """Retrieve a specific quiz, including its paginated questions"""
#     try:
#         user_id = get_jwt_identity()
#         quiz = Quiz.query.get(quiz_id)

#         if not quiz:
#             return jsonify({
#                 "success": False,
#                 "error": "Quiz not found"
#             }), 404

#         if not quiz.public and (quiz.created_by != user_id):
#             return jsonify({
#                 "success": False,
#                 "error": "Unauthorized access"
#             }), 403

#         try:
#             page = int(request.args.get('page', '1'))
#             per_page = int(request.args.get('limit', '10'))
#             if page <= 0 or per_page <= 0:
#                 raise ValueError("Pagination values must be positive integers")
#         except ValueError as ve:
#             return jsonify({
#                 "success": False,
#                 "error": "Bad Request",
#                 "message": "Pagination values must be positive integers."
#             }), 400

#         paginated_questions = (
#             Question.query.filter_by(quiz_id=quiz_id)
#             .paginate(page=page, per_page=per_page, error_out=False)
#         )
#         total = paginated_questions.total
#         pages = paginated_questions.pages

#         questions = [
#             OrderedDict([
#                 ("id", question.id),
#                 ("question_type", question.question_type),
#                 ("question_text", question.question_text),
#                 ("points", question.points),
#                 ("is_multiple_response", question.is_multiple_response),
#                 ("answer_choices", [
#                     OrderedDict([
#                         ("id", answer_choice.id),
#                         ("text", answer_choice.text),
#                         ("is_correct", answer_choice.is_correct)
#                     ])
#                     for answer_choice in question.answer_choices
#                 ])
#             ])
#             for question in paginated_questions.items
#         ]

#         result = [
#             OrderedDict([
#                 ("id", quiz.id),
#                 ("title", quiz.title),
#                 ("description", quiz.description),
#                 ("duration", f'{quiz.duration} minute(s)'),
#                 ("category", quiz.related_category.name
#                     if quiz.related_category else None),
#                 ("public", quiz.public),
#                 ("question_count", len(quiz.questions)),
#                 ("max_score", quiz.max_score),
#                 ("created_at", quiz.created_at.strftime('%Y-%m-%d')),
#                 ("questions", questions),
#             ])
#         ]

#         # HATEOAS links
#         links = OrderedDict({
#             "self": url_for('api_v1.get_quiz', quiz_id=quiz_id, page=page,
#                             limit=per_page, _external=True),
#             "next": url_for('api_v1.get_quiz', quiz_id=quiz_id,
#                             page=page+1, limit=per_page, _external=True)
#             if paginated_questions.has_next else None,
#             "prev": url_for('api_v1.get_quiz', quiz_id=quiz_id,
#                             page=page-1, limit=per_page, _external=True)
#             if paginated_questions.has_prev else None,
#             "first": url_for('api_v1.get_quiz', quiz_id=quiz_id, page=1,
#                              limit=per_page, _external=True),
#             "last": url_for('api_v1.get_quiz', quiz_id=quiz_id,
#                             page=pages, limit=per_page,
#                             _external=True) if pages > 0 else None
#         })

#         response_data = OrderedDict({
#             "success": True,
#             "data": result,
#             "total_items": total,
#             "total_pages": pages,
#             "links": links
#         })
#         response_json = json.dumps(response_data, default=str, sort_keys=False)
#         return Response(response_json, status=200, mimetype='application/json')

#     except ValueError as ve:
#         logger.error(f"ValueError: {ve}")
#         return jsonify({
#             "success": False,
#             "error": "Bad Request",
#             "message": "Pagination values must be positive integers"
#         }), 400

#     except Exception as e:
#         logger.error(f"Unexpected error in get_quiz: {e}")
#         return jsonify({
#             "success": False,
#             "error": "Internal Server Error",
#             "details": "An unexpected error occurred."
#         }), 500


# @api_v1.route('/quiz/<quiz_id>', methods=['PUT'])
# @jwt_required()
# @limiter.limit("10 per minute")
# def update_quiz(quiz_id):
#     """Update the details of a specific quiz"""
#     try:
#         if not request.is_json:
#             return jsonify({
#                 "success": False,
#                 "error": "Invalid JSON",
#                 "details": "Request content must be 'application/json'"
#             }), 400

#         try:
#             data = request.get_json()
#         except Exception as parse_error:
#             return jsonify({
#                 "success": False,
#                 "error": "Failed to parse JSON",
#                 "details": str(parse_error)
#             }), 400

#         if not data:
#             return jsonify({
#                 "success": False,
#                 "error": "Invalid input",
#                 "message": "Request body is missing or malformed"
#             }), 400

#         quiz = Quiz.query.get(quiz_id)
#         if not quiz:
#             return jsonify({"succes": False, "error": "Quiz not found"}), 404

#         user_id = get_jwt_identity()
#         if quiz.created_by != user_id:
#             return jsonify({
#                 "success": False,
#                 "error": "Unauthorized to update this quiz"
#             }), 403

#         if 'title' in data:
#             quiz.title = data['title']
#         if 'description' in data:
#             quiz.description = data['description']
#         if 'duration' in data:
#             try:
#                 quiz.duration = int(data['duration'])
#                 if quiz.duration <= 0:
#                     raise ValueError("Duration must be a positive integer")
#             except ValueError as ve:
#                 return jsonify({
#                     "success": False,
#                     "error": "Invalid input",
#                     "message": "Duration must be a positive integer"
#                 }), 400
#         if 'public' in data:
#             if not isinstance(data['public'], bool):
#                 return jsonify({
#                     "success": False,
#                     "error": "Invalid input",
#                     "message": "Public must be a boolean"
#                 }), 400
#             quiz.public = data['public']

#         quiz.calculate_max_score()
#         db.session.commit()
#         return jsonify({
#             "success": True,
#             "message": "Quiz updated successfully"
#         }), 200
#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Unexpected error in update_quiz: {e}")
#         return jsonify({
#             "success": False,
#             "error": "Failed to update quiz"
#         }), 400


# @api_v1.route('/quiz/<quiz_id>', methods=['DELETE'])
# @jwt_required()
# @limiter.limit("10 per minute")
# def delete_quiz(quiz_id):
#     """Delete a quiz"""
#     try:
#         if not request.is_json:
#             return jsonify({
#                 "success": False,
#                 "error": "Invalid JSON",
#                 "details": "Request content must be 'application/json'"
#             }), 400

#         try:
#             data = request.get_json()
#         except Exception as parse_error:
#             return jsonify({
#                 "success": False,
#                 "error": "Failed to parse JSON",
#                 "details": str(parse_error)
#             }), 400

#         user_id = get_jwt_identity()
#         quiz = Quiz.query.get(quiz_id)
#         if not quiz:
#             return jsonify({"succes": False, "error": "Quiz not found"}), 404

#         if quiz.created_by != user_id:
#             return jsonify({
#                 "success": False,
#                 "error": "Unauthorized to delete this quiz"
#             }), 403

#         db.session.delete(quiz)
#         db.session.commit()
#         return '', 204
#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Unexpected error in delete_quiz: {e}")
#         return jsonify({
#             "success": False,
#             "error": "Failed to delete quiz"
#         }), 400
