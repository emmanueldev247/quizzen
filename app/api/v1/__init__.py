from flask import Blueprint

api_v1 = Blueprint('api_v1', __name__, url_prefix='/quizzen/api/v1')

from . import auth, quizzes, questions
